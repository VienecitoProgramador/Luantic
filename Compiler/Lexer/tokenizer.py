"""
tokenizer.py
Analizador lexico de EntityScript.

Responsabilidad unica: convertir el texto fuente (.es) en una lista de Tokens
mas una comment_table lateral, SIN decidir nada de gramatica (eso es el Parser).

Contrato de salida:
    tokens: list[Token]          -> stream filtrado, SIN comentarios, listo para el Parser
    comment_table: list[dict]    -> [{"line": int, "text": str, "kind": "line"|"block"}]
                                     usado por Editor/lsp y por Transpiler (--preserve-comments)

Decisiones clave de diseño reflejadas aqui (ver Docs/language_spec.md):
- No existe 'end': los bloques cierran con '}' -> no hay logica de indentation-sensitivity.
- Comentarios: '#' de linea, '###' de bloque. Se tokenizan pero se filtran del stream
  que ve el Parser (arquitectura de 'comment_table' descrita en el design doc).
- Alias prohibidos de acciones (remove/delete/kill por destroy) generan error temprano,
  para reforzar 'una unica forma de hacer las cosas'.
"""

from .token_types import Token, TokenType, KEYWORDS, TYPES
from .lexer_errors import (
    UnterminatedStringError,
    UnterminatedBlockCommentError,
    UnexpectedCharacterError,
    ForbiddenAliasError,
)

# Alias prohibidos -> sugerencia correcta. Enforcement de "una unica forma de hacer las cosas".
FORBIDDEN_ACTION_ALIASES = {
    "remove": "destroy",
    "delete": "destroy",
    "kill": "destroy",
    "eliminate": "destroy",
}

SINGLE_CHAR_TOKENS = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
    ":": TokenType.COLON,
    "@": TokenType.AT,
    ".": TokenType.DOT,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<script>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self.comment_table: list[dict] = []

    # ---------------- utilidades de cursor ----------------

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= len(self.source):
            return "\0"
        return self.source[idx]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    # ---------------- entrada principal ----------------

    def tokenize(self) -> tuple[list[Token], list[dict]]:
        while not self._at_end():
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.col))
        return self.tokens, self.comment_table

    def _scan_token(self):
        start_line, start_col = self.line, self.col
        ch = self._advance()

        if ch in (" ", "\t", "\r"):
            return

        if ch == "\n" or ch == ";":
            self.tokens.append(Token(TokenType.NEWLINE, ch, None, start_line, start_col))
            return

        if ch == "#":
            self._scan_comment(start_line, start_col)
            return

        if ch == '"':
            self._scan_string(start_line, start_col)
            return

        if ch.isdigit():
            self._scan_number(ch, start_line, start_col)
            return

        if ch.isalpha() or ch == "_":
            self._scan_identifier_or_keyword(ch, start_line, start_col)
            return

        # Operadores multi-caracter
        if ch == "=":
            if self._match("="):
                self.tokens.append(Token(TokenType.EQ, "==", None, start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.ASSIGN, "=", None, start_line, start_col))
            return

        if ch == "!":
            if self._match("="):
                self.tokens.append(Token(TokenType.NEQ, "!=", None, start_line, start_col))
                return
            raise UnexpectedCharacterError("!", start_line, start_col)

        if ch == "+":
            if self._match("="):
                self.tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", None, start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.PLUS, "+", None, start_line, start_col))
            return

        if ch == "-":
            # Rechazo explicito de comentarios estilo Lua, antes de tratarlo
            # como operador: '--' nunca es valido en EntityScript.
            if self._peek() == "-":
                raise UnexpectedCharacterError("--", start_line, start_col)
            if self._match("="):
                self.tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", None, start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.MINUS, "-", None, start_line, start_col))
            return

        if ch == "*":
            if self._match("="):
                self.tokens.append(Token(TokenType.STAR_ASSIGN, "*=", None, start_line, start_col))
                return
            raise UnexpectedCharacterError("*", start_line, start_col)

        if ch == "/":
            if self._match("="):
                self.tokens.append(Token(TokenType.SLASH_ASSIGN, "/=", None, start_line, start_col))
                return
            raise UnexpectedCharacterError("/", start_line, start_col)

        if ch == ">":
            if self._match("="):
                self.tokens.append(Token(TokenType.GTE, ">=", None, start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.GT, ">", None, start_line, start_col))
            return

        if ch == "<":
            if self._match("="):
                self.tokens.append(Token(TokenType.LTE, "<=", None, start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.LT, "<", None, start_line, start_col))
            return

        if ch in SINGLE_CHAR_TOKENS:
            self.tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, None, start_line, start_col))
            return

        raise UnexpectedCharacterError(ch, start_line, start_col)

    # ---------------- comentarios ----------------

    def _scan_comment(self, start_line: int, start_col: int):
        # Bloque: ### ... ###
        if self._peek() == "#" and self._peek(1) == "#":
            self._advance()  # segundo #
            self._advance()  # tercer #
            text_chars = []
            closed = False
            while not self._at_end():
                if self._peek() == "#" and self._peek(1) == "#" and self._peek(2) == "#":
                    self._advance()
                    self._advance()
                    self._advance()
                    closed = True
                    break
                text_chars.append(self._advance())
            if not closed:
                raise UnterminatedBlockCommentError(start_line, start_col)
            text = "".join(text_chars).strip()
            self.comment_table.append({"line": start_line, "text": text, "kind": "block"})
            return

        # Linea: # ... hasta newline
        text_chars = []
        while not self._at_end() and self._peek() != "\n":
            text_chars.append(self._advance())
        text = "".join(text_chars).strip()
        self.comment_table.append({"line": start_line, "text": text, "kind": "line"})

    # ---------------- strings ----------------

    def _scan_string(self, start_line: int, start_col: int):
        chars = []
        while not self._at_end() and self._peek() != '"':
            chars.append(self._advance())
        if self._at_end():
            raise UnterminatedStringError(start_line, start_col)
        self._advance()  # cerrar comilla
        value = "".join(chars)
        self.tokens.append(Token(TokenType.STRING, value, value, start_line, start_col))

    # ---------------- numeros ----------------

    def _scan_number(self, first: str, start_line: int, start_col: int):
        chars = [first]
        while self._peek().isdigit():
            chars.append(self._advance())
        if self._peek() == "." and self._peek(1).isdigit():
            chars.append(self._advance())
            while self._peek().isdigit():
                chars.append(self._advance())
        text = "".join(chars)
        self.tokens.append(Token(TokenType.NUMBER, text, float(text), start_line, start_col))

    # ---------------- identificadores / keywords ----------------

    def _scan_identifier_or_keyword(self, first: str, start_line: int, start_col: int):
        chars = [first]
        while self._peek().isalnum() or self._peek() == "_":
            chars.append(self._advance())
        text = "".join(chars)

        # Enforcement de "una unica forma de hacer las cosas"
        if text in FORBIDDEN_ACTION_ALIASES:
            raise ForbiddenAliasError(text, FORBIDDEN_ACTION_ALIASES[text], start_line, start_col)

        if text in TYPES:
            self.tokens.append(Token(TYPES[text], text, None, start_line, start_col))
            return

        if text in KEYWORDS:
            self.tokens.append(Token(KEYWORDS[text], text, None, start_line, start_col))
            return

        # action_name reservados se resuelven aqui como IDENTIFIER especial:
        # el Parser los reconoce por lexema dentro de action_call.
        self.tokens.append(Token(TokenType.IDENTIFIER, text, None, start_line, start_col))


def tokenize_source(source: str, filename: str = "<script>") -> tuple[list[Token], list[dict]]:
    """Punto de entrada conveniente para Parser/CLI/Tests."""
    lexer = Lexer(source, filename)
    return lexer.tokenize()
