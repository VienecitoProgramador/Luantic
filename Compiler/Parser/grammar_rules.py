"""
grammar_rules.py
Parser recursive-descent para EntityScript, implementando 1:1 la EBNF del
design doc (program, entity_decl, event_block, statement, expression...).

Entrada: token stream ya filtrado de comentarios (ver Compiler/Lexer/tokenizer.py)
         + comment_table lateral para asociar comentarios a nodos (leading_comment).
Salida: nodo Program (raiz del AST, ver Compiler/AST/nodes.py).

Estrategia: recursive descent LL(1), una funcion _parse_x por cada regla EBNF.
Esto es deliberado: la gramatica de ES es simple por diseño (ver "Zero
Boilerplate" y ausencia de "end"), por lo que no se requiere un generador de
parsers (yacc/ANTLR) — un parser escrito a mano es mas facil de mantener y
de dar buenos mensajes de error, que es una prioridad del proyecto.
"""

from ..Lexer.token_types import Token, TokenType
from ..AST import nodes as n
from .syntax_errors import (
    UnexpectedTokenError,
    EntityNameCaseError,
    UnknownEventError,
    UnknownTagError,
    UnsupportedOperatorError,
    GlobalEventOnNonGlobalEntityError,
)

# event_name reservados segun la EBNF -- v0.1 + v0.2
KNOWN_EVENTS = {
    "touch", "spawn", "destroy", "click", "damage", "interact", "timer",
    "join", "leave", "death", "respawn",
}

# Eventos que solo tienen sentido en entidades @global (logica de servidor,
# no objetos fisicos). Ver design doc v0.2, seccion 4.
GLOBAL_ONLY_EVENTS = {"join", "leave", "death", "respawn"}

# action_name reservados segun la EBNF -- v0.1 + v0.2
KNOWN_ACTIONS = {
    "destroy", "spawn", "give", "play", "wait", "print",
    "take", "set", "heal", "damage", "teleport", "message", "find",
}

# tags conocidos en v0.1 + v0.2 (whitelist inicial; futuras versiones permiten tags custom via plugins)
KNOWN_TAGS = {"locked", "respawnable", "serveronly", "clientonly", "global", "interval"}

# Propiedades fisicas reservadas (v0.2) - cada una con tipo esperado fijo
PHYSICAL_PROPERTIES = {
    "position", "rotation", "size", "color",
    "material", "anchored", "collision", "transparency",
}

# Whitelist de nombres de color reservados (v0.2)
COLOR_NAMES = {
    "red", "blue", "green", "yellow", "white", "black",
    "gray", "orange", "purple", "pink", "brown", "cyan",
}


def _levenshtein_suggestion(word: str, candidates: set) -> str | None:
    """Sugerencia simple case-insensitive para mensajes de error tipo '"Touch" -> "touch"?'."""
    lowered = word.lower()
    if lowered in candidates:
        return lowered
    return None


class Parser:
    def __init__(self, tokens: list[Token], comment_table: list[dict]):
        self.tokens = tokens
        self.pos = 0
        # Indexamos comentarios por linea para lookup O(1) al construir nodos.
        self.comments_by_line = {c["line"]: c["text"] for c in comment_table}

    # ---------------- utilidades de cursor ----------------

    def _peek(self, offset: int = 0) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def _current(self) -> Token:
        return self._peek()

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _check(self, type_: TokenType) -> bool:
        return self._current().type == type_

    def _match(self, *types: TokenType) -> bool:
        if self._current().type in types:
            self._advance()
            return True
        return False

    def _expect(self, type_: TokenType, expected_desc: str) -> Token:
        if self._check(type_):
            return self._advance()
        found = self._current()
        raise UnexpectedTokenError(found.lexeme or found.type.name, expected_desc, found.line)

    def _skip_newlines(self):
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _leading_comment_for(self, line: int) -> str | None:
        return self.comments_by_line.get(line - 1) or self.comments_by_line.get(line)

    # ---------------- program ----------------

    def parse_program(self) -> n.Program:
        imports = []
        entities = []
        leaderstats = []
        self._skip_newlines()
        while not self._check(TokenType.EOF):
            if self._check(TokenType.USE):
                imports.append(self._parse_import())
            elif self._check(TokenType.LEADERSTAT):
                leaderstats.append(self._parse_leaderstat())
            elif self._check(TokenType.ENTITY):
                entities.append(self._parse_entity())
            else:
                tok = self._current()
                raise UnexpectedTokenError(tok.lexeme, '"entity", "use" o "leaderstat"', tok.line)
            self._skip_newlines()
        return n.Program(imports=imports, entities=entities, leaderstats=leaderstats, line=1)

    def _parse_leaderstat(self) -> n.LeaderstatDecl:
        line = self._current().line
        self._expect(TokenType.LEADERSTAT, '"leaderstat"')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre del leaderstat")
        self._expect(TokenType.ASSIGN, '"="')
        num_tok = self._expect(TokenType.NUMBER, "un numero inicial")
        return n.LeaderstatDecl(name=name_tok.lexeme, initial=num_tok.literal, line=line)

    def _parse_import(self) -> n.ImportDecl:
        line = self._current().line
        self._expect(TokenType.USE, '"use"')
        path = [self._expect(TokenType.IDENTIFIER, "un identificador").lexeme]
        while self._match(TokenType.DOT):
            path.append(self._expect(TokenType.IDENTIFIER, "un identificador").lexeme)
        self._skip_newlines()
        return n.ImportDecl(path=path, line=line)

    # ---------------- entity_decl ----------------

    def _parse_entity(self) -> n.EntityDecl:
        line = self._current().line
        comment = self._leading_comment_for(line)
        self._expect(TokenType.ENTITY, '"entity"')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre de la entidad")

        if not name_tok.lexeme[0].isupper():
            raise EntityNameCaseError(name_tok.lexeme, name_tok.line)

        parent = None
        if self._match(TokenType.EXTENDS):
            parent = self._expect(TokenType.IDENTIFIER, "el nombre de la entidad padre").lexeme

        self._expect(TokenType.LBRACE, '"{"')
        self._skip_newlines()

        properties: list[n.PropertyDecl] = []
        events: list[n.EventBlock] = []
        tags: list[n.TagDecl] = []
        functions: list[n.FunctionDecl] = []
        consts: list[n.ConstDecl] = []
        physical_props: list[n.PhysicalProperty] = []
        score_binding: n.ScoreBinding | None = None

        while not self._check(TokenType.RBRACE):
            if self._check(TokenType.AT):
                tags.append(self._parse_tag())
            elif self._check(TokenType.ON):
                events.append(self._parse_event_block())
            elif self._check(TokenType.FUNCTION):
                functions.append(self._parse_function_decl())
            elif self._check(TokenType.CONST):
                consts.append(self._parse_const_decl())
            elif self._check(TokenType.SCORE):
                score_binding = self._parse_score_binding()
            elif self._check(TokenType.IDENTIFIER) and self._current().lexeme in PHYSICAL_PROPERTIES:
                physical_props.append(self._parse_physical_property())
            elif self._check(TokenType.IDENTIFIER):
                properties.append(self._parse_property())
            else:
                tok = self._current()
                raise UnexpectedTokenError(
                    tok.lexeme,
                    'una propiedad, un tag "@", "function", "const" o un bloque "on"',
                    tok.line,
                )
            self._skip_newlines()

        self._expect(TokenType.RBRACE, '"}"')

        is_global = any(t.name == "global" for t in tags)
        for event in events:
            if event.event_name in GLOBAL_ONLY_EVENTS and not is_global:
                raise GlobalEventOnNonGlobalEntityError(event.event_name, name_tok.lexeme, event.line)

        return n.EntityDecl(
            name=name_tok.lexeme,
            parent=parent,
            properties=properties,
            events=events,
            tags=tags,
            functions=functions,
            consts=consts,
            score_binding=score_binding,
            physical_props=physical_props,
            line=line,
            leading_comment=comment,
        )

    def _parse_tag(self) -> n.TagDecl:
        line = self._current().line
        self._expect(TokenType.AT, '"@"')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre del tag")

        if name_tok.lexeme.lower() not in KNOWN_TAGS or name_tok.lexeme != name_tok.lexeme.lower():
            if name_tok.lexeme != name_tok.lexeme.lower():
                raise UnknownTagError(name_tok.lexeme, name_tok.line)

        args = []
        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_expression())
                while self._match(TokenType.COMMA):
                    args.append(self._parse_expression())
            self._expect(TokenType.RPAREN, '")"')
        return n.TagDecl(name=name_tok.lexeme, args=args, line=line)

    def _parse_property(self) -> n.PropertyDecl:
        line = self._current().line
        comment = self._leading_comment_for(line)
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre de la propiedad")

        type_annotation = None
        if self._match(TokenType.COLON):
            type_annotation = self._advance().lexeme  # type_annotation explicita (TYPE_* o IDENTIFIER)

        self._expect(TokenType.ASSIGN, '"="')
        value = self._parse_expression()

        if type_annotation is None:
            type_annotation = self._infer_type(value)

        return n.PropertyDecl(
            name=name_tok.lexeme,
            type_annotation=type_annotation,
            default_value=value,
            line=line,
            leading_comment=comment,
        )

    @staticmethod
    def _infer_type(expr: n.Expr) -> str:
        """
        Inferencia de tipos v0.2: si no hay ':Tipo' explicito, se infiere del
        literal. Solo se infieren los 4 tipos con literal inequivoco; tipos
        especiales de Roblox (Sound, Model) siguen requiriendo anotacion
        explicita porque su representacion literal (un string) es ambigua
        con String real.
        """
        if isinstance(expr, n.Literal):
            if expr.literal_kind == "number":
                return "Number"
            if expr.literal_kind == "string":
                return "String"
            if expr.literal_kind == "boolean":
                return "Bool"
            if expr.literal_kind == "vector3":
                return "Vector3"
            if expr.literal_kind in ("colorname", "hexcolor"):
                return "Color"
        return "Number"  # fallback conservador, no deberia alcanzarse en la practica

    def _parse_const_decl(self) -> n.ConstDecl:
        line = self._current().line
        self._expect(TokenType.CONST, '"const"')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre de la constante")
        self._expect(TokenType.ASSIGN, '"="')
        value = self._parse_expression()
        return n.ConstDecl(name=name_tok.lexeme, value=value, line=line)

    def _parse_score_binding(self) -> n.ScoreBinding:
        line = self._current().line
        self._expect(TokenType.SCORE, '"score"')
        self._expect(TokenType.ASSIGN, '"="')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre del leaderstat")
        return n.ScoreBinding(leaderstat_name=name_tok.lexeme, line=line)

    def _parse_physical_property(self) -> n.PhysicalProperty:
        line = self._current().line
        name_tok = self._advance()  # ya validado que esta en PHYSICAL_PROPERTIES
        self._expect(TokenType.ASSIGN, '"="')
        value = self._parse_expression()
        return n.PhysicalProperty(name=name_tok.lexeme, value=value, line=line)

    def _parse_function_decl(self) -> n.FunctionDecl:
        line = self._current().line
        comment = self._leading_comment_for(line)
        self._expect(TokenType.FUNCTION, '"function"')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre de la funcion")
        self._expect(TokenType.LPAREN, '"("')
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._parse_param_name())
            while self._match(TokenType.COMMA):
                params.append(self._parse_param_name())
        self._expect(TokenType.RPAREN, '")"')
        self._expect(TokenType.LBRACE, '"{"')
        body = self._parse_statement_list()
        self._expect(TokenType.RBRACE, '"}"')
        return n.FunctionDecl(name=name_tok.lexeme, params=params, body=body, line=line, leading_comment=comment)

    def _parse_param_name(self) -> str:
        """
        Nombres de parametro de evento aceptan IDENTIFIER normal o la
        palabra reservada 'player', ya que `on touch(player)` es el caso
        de uso mas comun del lenguaje y 'player' es semanticamente valido
        como nombre de parametro (no colisiona con PlayerRef como expresion,
        que solo se usa dentro del cuerpo del evento).
        """
        tok = self._current()
        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return tok.lexeme
        if tok.type == TokenType.PLAYER_KW:
            self._advance()
            return "player"
        raise UnexpectedTokenError(tok.lexeme or tok.type.name, "un parametro", tok.line)

    # ---------------- event_block ----------------

    def _parse_event_block(self) -> n.EventBlock:
        line = self._current().line
        comment = self._leading_comment_for(line)
        self._expect(TokenType.ON, '"on"')
        event_tok = self._expect(TokenType.IDENTIFIER, "el nombre del evento")

        event_name = event_tok.lexeme
        if event_name not in KNOWN_EVENTS:
            suggestion = _levenshtein_suggestion(event_name, KNOWN_EVENTS)
            raise UnknownEventError(event_name, suggestion, event_tok.line)

        params = []
        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                params.append(self._parse_param_name())
                while self._match(TokenType.COMMA):
                    params.append(self._parse_param_name())
            self._expect(TokenType.RPAREN, '")"')

        self._expect(TokenType.LBRACE, '"{"')
        self._skip_newlines()
        body = self._parse_statement_list()
        self._expect(TokenType.RBRACE, '"}"')

        return n.EventBlock(
            event_name=event_name, params=params, body=body, line=line, leading_comment=comment
        )

    # ---------------- statement list ----------------

    def _parse_statement_list(self) -> list[n.Stmt]:
        statements = []
        self._skip_newlines()
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            statements.append(self._parse_statement())
            self._skip_newlines()
        return statements

    def _parse_statement(self) -> n.Stmt:
        tok = self._current()
        comment = self._leading_comment_for(tok.line)
        stmt = self._parse_statement_inner(tok)
        if comment is not None:
            stmt.leading_comment = comment
        return stmt

    def _parse_statement_inner(self, tok) -> n.Stmt:

        if tok.type == TokenType.IF:
            return self._parse_conditional()

        if tok.type == TokenType.REPEAT:
            return self._parse_loop()

        if tok.type == TokenType.AFTER:
            return self._parse_after()

        if tok.type == TokenType.FOR:
            return self._parse_for()

        if tok.type == TokenType.EMIT:
            return self._parse_emit()

        if tok.type == TokenType.IDENTIFIER and tok.lexeme in KNOWN_ACTIONS:
            return self._parse_action_call()

        if tok.type == TokenType.IDENTIFIER:
            next_tok = self._peek(1)
            if next_tok.type == TokenType.LPAREN:
                return self._parse_function_call()
            if next_tok.type in (
                TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN,
            ):
                return self._parse_assignment()
            return self._parse_action_call()

        raise UnexpectedTokenError(tok.lexeme or tok.type.name, "una sentencia valida", tok.line)

    def _parse_function_call(self) -> n.FunctionCall:
        line = self._current().line
        name_tok = self._advance()
        self._expect(TokenType.LPAREN, '"("')
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                args.append(self._parse_expression())
        self._expect(TokenType.RPAREN, '")"')
        return n.FunctionCall(name=name_tok.lexeme, args=args, line=line)

    def _parse_assignment(self) -> n.Assignment:
        line = self._current().line
        target_tok = self._expect(TokenType.IDENTIFIER, "un identificador")

        op_tok = self._current()
        op_map = {
            TokenType.ASSIGN: "=",
            TokenType.PLUS_ASSIGN: "+=",
            TokenType.MINUS_ASSIGN: "-=",
            TokenType.STAR_ASSIGN: "*=",
            TokenType.SLASH_ASSIGN: "/=",
        }
        if op_tok.type not in op_map:
            raise UnsupportedOperatorError(op_tok.lexeme, op_tok.line)
        operator = op_map[op_tok.type]
        self._advance()

        value = self._parse_expression()
        return n.Assignment(target=target_tok.lexeme, operator=operator, value=value, line=line)

    def _parse_action_call(self) -> n.ActionCall:
        line = self._current().line
        name_tok = self._advance()
        args = []

        # `message` acepta destinatarios especiales: all, team <Nombre>, ademas de player
        if name_tok.lexeme == "message" and self._check(TokenType.ALL_KW):
            self._advance()
            args.append(n.Literal(value="all", literal_kind="string", line=line))
            while not self._check(TokenType.NEWLINE) and not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
                args.append(self._parse_term())
            return n.ActionCall(action_name=name_tok.lexeme, args=args, line=line)

        if name_tok.lexeme == "message" and self._check(TokenType.TEAM_KW):
            self._advance()
            team_name_tok = self._expect(TokenType.IDENTIFIER, "el nombre del equipo")
            args.append(n.Literal(value=f"team:{team_name_tok.lexeme}", literal_kind="string", line=line))
            while not self._check(TokenType.NEWLINE) and not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
                args.append(self._parse_term())
            return n.ActionCall(action_name=name_tok.lexeme, args=args, line=line)

        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_expression())
                while self._match(TokenType.COMMA):
                    args.append(self._parse_expression())
            self._expect(TokenType.RPAREN, '")"')
        else:
            # Sintaxis sin parentesis: los argumentos van separados por espacio,
            # sin coma (ej. `give player points`, `play sound`, `print "texto"`).
            # Se detiene al llegar a newline, `}` o EOF.
            while not self._check(TokenType.NEWLINE) and not self._check(
                TokenType.RBRACE
            ) and not self._check(TokenType.EOF):
                args.append(self._parse_term())

        return n.ActionCall(action_name=name_tok.lexeme, args=args, line=line)

    def _parse_conditional(self) -> n.Conditional:
        line = self._current().line
        self._expect(TokenType.IF, '"if"')
        condition = self._parse_expression()
        self._expect(TokenType.LBRACE, '"{"')
        then_branch = self._parse_statement_list()
        self._expect(TokenType.RBRACE, '"}"')

        else_branch = None
        if self._match(TokenType.ELSE):
            self._expect(TokenType.LBRACE, '"{"')
            else_branch = self._parse_statement_list()
            self._expect(TokenType.RBRACE, '"}"')

        return n.Conditional(
            condition=condition, then_branch=then_branch, else_branch=else_branch, line=line
        )

    def _parse_loop(self) -> n.Loop:
        line = self._current().line
        self._expect(TokenType.REPEAT, '"repeat"')
        count_expr = self._parse_expression()
        self._expect(TokenType.TIMES, '"times"')
        self._expect(TokenType.LBRACE, '"{"')
        body = self._parse_statement_list()
        self._expect(TokenType.RBRACE, '"}"')
        return n.Loop(count_expr=count_expr, body=body, line=line)

    def _parse_after(self) -> n.AfterStmt:
        line = self._current().line
        self._expect(TokenType.AFTER, '"after"')
        delay_expr = self._parse_expression()
        self._expect(TokenType.LBRACE, '"{"')
        body = self._parse_statement_list()
        self._expect(TokenType.RBRACE, '"}"')
        return n.AfterStmt(delay_expr=delay_expr, body=body, line=line)

    def _parse_for(self) -> n.ForStmt:
        line = self._current().line
        self._expect(TokenType.FOR, '"for"')
        var_name = self._parse_param_name()
        self._expect(TokenType.IN, '"in"')
        self._expect(TokenType.PLAYERS, '"players"')
        self._expect(TokenType.LBRACE, '"{"')
        body = self._parse_statement_list()
        self._expect(TokenType.RBRACE, '"}"')
        return n.ForStmt(var_name=var_name, collection="players", body=body, line=line)

    def _parse_emit(self) -> n.EmitStmt:
        line = self._current().line
        self._expect(TokenType.EMIT, '"emit"')
        name_tok = self._expect(TokenType.IDENTIFIER, "el nombre del evento a emitir")
        args = []
        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_expression())
                while self._match(TokenType.COMMA):
                    args.append(self._parse_expression())
            self._expect(TokenType.RPAREN, '")"')
        return n.EmitStmt(event_name=name_tok.lexeme, args=args, line=line)

    # ---------------- expression ----------------

    _COMPARATORS = {
        TokenType.EQ: "==",
        TokenType.NEQ: "!=",
        TokenType.GT: ">",
        TokenType.LT: "<",
        TokenType.GTE: ">=",
        TokenType.LTE: "<=",
    }
    _ADDITIVE = {
        TokenType.PLUS: "+",
        TokenType.MINUS: "-",
        TokenType.AND: "and",
        TokenType.OR: "or",
    }

    def _parse_expression(self) -> n.Expr:
        left = self._parse_term()
        while self._current().type in self._COMPARATORS or self._current().type in self._ADDITIVE:
            op_tok = self._advance()
            operator = self._COMPARATORS.get(op_tok.type) or self._ADDITIVE.get(op_tok.type)
            right = self._parse_term()
            left = n.BinaryExpr(left=left, operator=operator, right=right, line=op_tok.line)
        return left

    def _parse_term(self) -> n.Expr:
        tok = self._current()

        # Numero negativo: unico uso permitido de '-' como prefijo unario.
        # Se resuelve aqui (no como BinaryExpr) porque `-5` es un LITERAL,
        # no una resta entre dos operandos -- evita ambiguedad con la regla
        # "una unica forma de hacer las cosas": no hay negacion unaria
        # generica en ES (ver Docs), solo se permite pegada a un numero.
        if tok.type == TokenType.MINUS and self._peek(1).type == TokenType.NUMBER:
            self._advance()  # consume '-'
            num_tok = self._advance()  # consume NUMBER
            return n.Literal(value=-num_tok.literal, literal_kind="number", line=tok.line)

        if tok.type == TokenType.LPAREN:
            # Puede ser subexpresion agrupada o vector3_literal (num, num, num)
            return self._parse_paren_expr()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return n.Literal(value=tok.literal, literal_kind="number", line=tok.line)

        if tok.type == TokenType.STRING:
            self._advance()
            if _is_hex_color(tok.literal):
                return n.Literal(value=tok.literal, literal_kind="hexcolor", line=tok.line)
            return n.Literal(value=tok.literal, literal_kind="string", line=tok.line)

        if tok.type == TokenType.TRUE:
            self._advance()
            return n.Literal(value=True, literal_kind="boolean", line=tok.line)

        if tok.type == TokenType.FALSE:
            self._advance()
            return n.Literal(value=False, literal_kind="boolean", line=tok.line)

        if tok.type == TokenType.SELF:
            self._advance()
            return n.SelfRef(line=tok.line)

        if tok.type == TokenType.PLAYER_KW:
            self._advance()
            return self._parse_member_chain(n.PlayerRef(line=tok.line))

        if tok.type == TokenType.ALL_KW:
            self._advance()
            return n.Literal(value="all", literal_kind="string", line=tok.line)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            if tok.lexeme in COLOR_NAMES:
                return n.Literal(value=tok.lexeme, literal_kind="colorname", line=tok.line)
            base = n.Identifier(name=tok.lexeme, line=tok.line)
            return self._parse_member_chain(base)

        raise UnexpectedTokenError(tok.lexeme or tok.type.name, "una expresion valida", tok.line)

    def _parse_member_chain(self, base: n.Expr) -> n.Expr:
        while self._match(TokenType.DOT):
            member_tok = self._expect(TokenType.IDENTIFIER, "un nombre de propiedad")
            base = n.MemberAccess(obj=base, member=member_tok.lexeme, line=member_tok.line)
        return base

    def _parse_paren_expr(self) -> n.Expr:
        line = self._current().line
        self._expect(TokenType.LPAREN, '"("')
        first = self._parse_expression()

        if self._check(TokenType.COMMA):
            # vector3_literal: (num, num, num)
            values = [first]
            while self._match(TokenType.COMMA):
                values.append(self._parse_expression())
            self._expect(TokenType.RPAREN, '")"')
            nums = tuple(v.value for v in values if isinstance(v, n.Literal))
            return n.Literal(value=nums, literal_kind="vector3", line=line)

        self._expect(TokenType.RPAREN, '")"')
        return first


def _is_hex_color(value: str) -> bool:
    """Un string literal es un color hex si tiene la forma exacta '#RRGGBB'."""
    if not value.startswith("#") or len(value) != 7:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in value[1:])


def parse_tokens(tokens: list[Token], comment_table: list[dict]) -> n.Program:
    """Punto de entrada conveniente para CLI/Tests."""
    parser = Parser(tokens, comment_table)
    return parser.parse_program()
