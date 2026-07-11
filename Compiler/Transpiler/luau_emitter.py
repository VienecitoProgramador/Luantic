"""
luau_emitter.py
Nucleo del Transpiler: recorre el AST (via ASTVisitor) y emite codigo Luau
idiomatico, legible y compatible 1:1 con el runtime en Runtime/es_stdlib.luau.

Decisiones de arquitectura reflejadas en este archivo (ver design doc seccion 4):
- Cada `entity` se convierte en un ModuleScript/Script Luau que asume
  `local self = script.Parent` (Roblox convention).
- Cada `on <event>` se traduce a UNA llamada a una funcion dispatcher de
  Runtime/event_dispatcher.luau (es_on_touch, es_on_damage, etc), nunca a
  logica de debounce/nil-check inline.
- Cada `action_name` reservado (give, play, destroy...) se traduce a una
  llamada corta a Runtime/es_stdlib.luau (es_give_stat, es_play_sound...).
- Todo simbolo de runtime esta prefijado con `es_` para garantizar
  "Total compatibilidad con Luau": el codigo generado puede coexistir con
  Luau escrito a mano sin colisionar en el namespace global.
- Si --preserve-comments esta activo, los `leading_comment` del AST se
  re-emiten como comentarios Luau (`--`) en el punto correspondiente,
  util para depurar el codigo generado.
"""

from ..AST import nodes as n
from ..AST.visitor import ASTVisitor
from ..Semantic.symbol_table import SymbolTable
from .templates.event_wrappers import wrap_event

INDENT = "    "

# Mapeo de propiedades fisicas ES -> propiedad real de BasePart en Luau
PHYSICAL_PROPERTY_LUAU_NAME = {
    "position": "Position",
    "rotation": "Orientation",
    "size": "Size",
    "color": "Color",
    "material": "Material",
    "anchored": "Anchored",
    "collision": "CanCollide",
    "transparency": "Transparency",
}

# Whitelist de nombres de color -> RGB, debe coincidir con Parser/grammar_rules.COLOR_NAMES
COLOR_NAME_TO_RGB = {
    "red": (255, 0, 0), "blue": (0, 0, 255), "green": (0, 255, 0), "yellow": (255, 255, 0),
    "white": (255, 255, 255), "black": (0, 0, 0), "gray": (128, 128, 128), "orange": (255, 165, 0),
    "purple": (128, 0, 128), "pink": (255, 192, 203), "brown": (139, 69, 19), "cyan": (0, 255, 255),
}

"""
Nota de arquitectura - representacion de propiedades:

Las `property_decl` de EntityScript se traducen a Instance Attributes de
Roblox (self:SetAttribute / self:GetAttribute), NO a variables `local`.

Se eligio este enfoque en vez de `local` por dos razones:
1. Herencia (`extends`): con `local`, cada entity es un script/scope Luau
   separado y una propiedad heredada de `Character` no seria visible
   dentro del scope de `Goblin`. Los Attributes viven en la INSTANCIA
   (self), no en el scope del script, por lo que se comparten
   naturalmente entre la logica propia y la heredada.
2. Inspeccionabilidad: los Attributes son visibles y editables en vivo
   desde Roblox Studio (panel Properties > Attributes), lo cual es una
   ventaja practica para diseñadores de nivel que ajustan balance sin
   tocar codigo.

El precio de este enfoque es una linea ligeramente mas larga por acceso
(`self:GetAttribute("health")` en vez de `health`), que el emitter
resuelve automaticamente reescribiendo cada Identifier que coincide con
una propiedad conocida de la entidad (ver `_is_known_property`).
"""


class PropertyResolver:
    """Determina si un identificador dentro de un evento es una property_decl
    (propia o heredada) para decidir si se emite como Attribute o como
    variable local corriente (ej. un parametro de evento como `amount`)."""

    def __init__(self, symbols: SymbolTable | None):
        self.symbols = symbols

    def is_property(self, entity_name: str, identifier: str) -> bool:
        if self.symbols is None:
            return False
        return self.symbols.resolve_property_type(entity_name, identifier) is not None

# action_name (ES) -> nombre de funcion en Runtime/es_stdlib.luau
# (give/take/set/heal/damage/teleport/message/find/destroy tienen logica propia
# en visit_ActionCall porque su forma de armar argumentos difiere de este patron simple)
ACTION_STDLIB_MAP = {
    "spawn": "es_spawn",
    "play": "es_play_sound",
    "wait": "es_wait",
    "print": "print",  # print es nativo de Luau, no requiere stdlib
}


class LuauEmitter(ASTVisitor):
    def __init__(self, preserve_comments: bool = False, symbols: SymbolTable | None = None):
        self.preserve_comments = preserve_comments
        self.resolver = PropertyResolver(symbols)
        self._current_entity: str | None = None
        self._local_names: set[str] = set()  # parametros de evento/funcion en el scope actual
        self._function_names: set[str] = set()  # funciones declaradas en la entidad actual

    # ---------------- entrada principal ----------------

    def emit_program(self, program: n.Program) -> dict[str, str]:
        """
        Retorna un dict {nombre_entidad: codigo_luau}, ya que en Roblox cada
        `entity` se despliega tipicamente como un Script/ModuleScript separado.
        """
        output = {}
        for entity in program.entities:
            output[entity.name] = self.visit(entity)
        return output

    # ---------------- entity ----------------

    def visit_EntityDecl(self, entity: n.EntityDecl) -> str:
        self._current_entity = entity.name
        self._function_names = {f.name for f in entity.functions}
        lines = []
        lines.append("local self = script.Parent")
        lines.append("")

        if entity.parent:
            lines.append(f'es_inherit(self, "{entity.parent}")')
            lines.append("")

        for c in entity.consts:
            lines.append(self._emit_comment_if_any(c))
            lines.append(self.visit(c))
        if entity.consts:
            lines.append("")

        for prop in entity.properties:
            lines.append(self._emit_comment_if_any(prop))
            lines.append(self.visit(prop))
        if entity.properties:
            lines.append("")

        for pp in entity.physical_props:
            lines.append(self.visit(pp))
        if entity.physical_props:
            lines.append("")

        if entity.score_binding:
            lines.append(f'self:SetAttribute("ESScoreTarget", "{entity.score_binding.leaderstat_name}")')
            lines.append("")

        for tag in entity.tags:
            if tag.name == "global":
                continue  # @global es metadata de compilacion (valida eventos), no genera runtime
            lines.append(self.visit(tag))
        if any(t.name != "global" for t in entity.tags):
            lines.append("")

        for fn in entity.functions:
            lines.append(self._emit_comment_if_any(fn))
            lines.append(self.visit(fn))
            lines.append("")

        for event in entity.events:
            lines.append(self._emit_comment_if_any(event))
            lines.append(self.visit(event))
            lines.append("")

        return "\n".join(l for l in lines if l is not None).rstrip() + "\n"

    def visit_ConstDecl(self, c: n.ConstDecl) -> str:
        # const se traduce a `local` real (no Attribute): nunca cambia, no
        # necesita persistir en la instancia ni ser editable desde Studio.
        value = self.visit(c.value)
        return f"local {c.name} = {value}"

    def visit_PhysicalProperty(self, pp: n.PhysicalProperty) -> str:
        luau_name = PHYSICAL_PROPERTY_LUAU_NAME[pp.name]
        if pp.name == "color":
            return f"self.{luau_name} = {self._emit_color(pp.value)}"
        value = self.visit(pp.value)
        return f"self.{luau_name} = {value}"

    def _emit_color(self, expr: n.Expr) -> str:
        if isinstance(expr, n.Literal) and expr.literal_kind == "colorname":
            r, g, b = COLOR_NAME_TO_RGB[expr.value]
            return f"Color3.fromRGB({r}, {g}, {b})"
        if isinstance(expr, n.Literal) and expr.literal_kind == "hexcolor":
            hexval = expr.value.lstrip("#")
            r, g, b = int(hexval[0:2], 16), int(hexval[2:4], 16), int(hexval[4:6], 16)
            return f"Color3.fromRGB({r}, {g}, {b})"
        if isinstance(expr, n.Literal) and expr.literal_kind == "vector3":
            r, g, b = expr.value
            return f"Color3.fromRGB({_format_number(r)}, {_format_number(g)}, {_format_number(b)})"
        return self.visit(expr)

    def visit_FunctionDecl(self, fn: n.FunctionDecl) -> str:
        previous_locals = self._local_names
        self._local_names = set(fn.params)

        params = ", ".join(fn.params)
        lines = [f"local function {fn.name}({params})"]
        for stmt in fn.body:
            comment = self._emit_comment_if_any(stmt)
            if comment:
                lines.append(self._indent(comment))
            lines.append(self._indent(self.visit(stmt)))
        lines.append("end")

        self._local_names = previous_locals
        return "\n".join(lines)

    def visit_PropertyDecl(self, prop: n.PropertyDecl) -> str:
        value = self.visit(prop.default_value)
        return f'self:SetAttribute("{prop.name}", {value})'

    def visit_TagDecl(self, tag: n.TagDecl) -> str:
        if tag.name == "interval":
            # @interval(N) configura el intervalo de `on timer`. Se traduce
            # directo al Attribute que event_dispatcher.es_on_timer ya lee,
            # en vez de pasar por es_apply_tag (mas simple y mas rapido).
            seconds = self.visit(tag.args[0]) if tag.args else "1"
            return f'self:SetAttribute("ESTimerInterval", {seconds})'
        args = ", ".join(self.visit(a) for a in tag.args)
        return f'es_apply_tag(self, "{tag.name}"{", " + args if args else ""})'

    # ---------------- event ----------------

    def visit_EventBlock(self, event: n.EventBlock) -> str:
        previous_locals = self._local_names
        self._local_names = set(event.params)

        body_lines = []
        for stmt in event.body:
            comment = self._emit_comment_if_any(stmt)
            if comment:
                body_lines.append(comment)
            body_lines.append(self.visit(stmt))
        body_code = "\n".join(body_lines)

        self._local_names = previous_locals
        return wrap_event(event.event_name, event.params, body_code, INDENT)

    # ---------------- statements ----------------

    def visit_Assignment(self, stmt: n.Assignment) -> str:
        value = self.visit(stmt.value)
        is_prop = self._is_property_ref(stmt.target)

        if is_prop:
            current = f'self:GetAttribute("{stmt.target}")'
        else:
            current = stmt.target

        if stmt.operator == "+=":
            new_value = f"{current} + {value}"
        elif stmt.operator == "-=":
            new_value = f"{current} - {value}"
        elif stmt.operator == "*=":
            new_value = f"{current} * {value}"
        elif stmt.operator == "/=":
            new_value = f"{current} / {value}"
        else:
            new_value = value

        if is_prop:
            return f'self:SetAttribute("{stmt.target}", {new_value})'
        return f"{stmt.target} = {new_value}"

    def visit_ActionCall(self, stmt: n.ActionCall) -> str:
        args = [self.visit(a) for a in stmt.args]
        name = stmt.action_name

        if name == "destroy":
            target = args[0] if args else "self"
            return f"{target}:Destroy()"

        if name in ("give", "take"):
            # give/take player amount -> es_modify_score(self, player, +/-amount)
            # usa el leaderstat indicado por `score = X` en la entidad actual.
            player_arg = args[0] if args else "player"
            amount_arg = args[1] if len(args) > 1 else "0"
            sign = "" if name == "give" else "-"
            return f"es_modify_score(self, {player_arg}, {sign}({amount_arg}))"

        if name == "set":
            player_arg = args[0] if args else "player"
            amount_arg = args[1] if len(args) > 1 else "0"
            return f"es_set_score(self, {player_arg}, {amount_arg})"

        if name == "heal":
            target = args[0] if args else "player"
            amount_arg = args[1] if len(args) > 1 else "0"
            return f"es_heal({target}, {amount_arg})"

        if name == "damage":
            # accion `damage`, distinta del evento `on damage`: no lo dispara
            # automaticamente, son independientes (ver Docs/language_spec.md).
            target = args[0] if args else "player"
            amount_arg = args[1] if len(args) > 1 else "0"
            return f"es_apply_damage({target}, {amount_arg})"

        if name == "teleport":
            target = args[0] if args else "player"
            destination = args[1] if len(args) > 1 else "nil"
            return f"es_teleport({target}, {destination})"

        if name == "message":
            target = args[0] if args else '"all"'
            text = args[1] if len(args) > 1 else '""'
            return f"es_message({target}, {text})"

        if name == "find":
            entity_name_arg = args[0] if args else '""'
            return f"es_find({entity_name_arg})"

        stdlib_fn = ACTION_STDLIB_MAP.get(name, name)
        arg_str = ", ".join(args)
        if name in ("play", "spawn", "wait"):
            # estas acciones siempre reciben `self` implicito como primer argumento,
            # seguido de los argumentos escritos por el usuario en el mismo orden
            prefix = "self" + (", " if arg_str else "")
            return f"{stdlib_fn}({prefix}{arg_str})"
        return f"{stdlib_fn}({arg_str})"

    def visit_FunctionCall(self, stmt: n.FunctionCall) -> str:
        args = ", ".join(self.visit(a) for a in stmt.args)
        return f"{stmt.name}({args})"

    def visit_AfterStmt(self, stmt: n.AfterStmt) -> str:
        delay = self.visit(stmt.delay_expr)
        lines = [f"task.delay({delay}, function()"]
        for s in stmt.body:
            lines.append(self._indent(self.visit(s)))
        lines.append("end)")
        return "\n".join(lines)

    def visit_ForStmt(self, stmt: n.ForStmt) -> str:
        # v0.2 solo soporta `for x in players`, unica coleccion disponible.
        previous_locals = self._local_names
        self._local_names = self._local_names | {stmt.var_name}

        lines = [f'for _, {stmt.var_name} in ipairs(game:GetService("Players"):GetPlayers()) do']
        for s in stmt.body:
            lines.append(self._indent(self.visit(s)))
        lines.append("end")

        self._local_names = previous_locals
        return "\n".join(lines)

    def visit_Conditional(self, stmt: n.Conditional) -> str:
        cond = self.visit(stmt.condition)
        lines = [f"if {cond} then"]
        for s in stmt.then_branch:
            lines.append(self._indent(self.visit(s)))
        if stmt.else_branch:
            lines.append("else")
            for s in stmt.else_branch:
                lines.append(self._indent(self.visit(s)))
        lines.append("end")
        return "\n".join(lines)

    def visit_Loop(self, stmt: n.Loop) -> str:
        count = self.visit(stmt.count_expr)
        lines = [f"for _es_i = 1, {count} do"]
        for s in stmt.body:
            lines.append(self._indent(self.visit(s)))
        lines.append("end")
        return "\n".join(lines)

    def visit_EmitStmt(self, stmt: n.EmitStmt) -> str:
        args = ", ".join(self.visit(a) for a in stmt.args)
        prefix = "self" + (", " if args else "")
        return f'es_emit("{stmt.event_name}", {prefix}{args})'

    # ---------------- expressions ----------------

    def visit_BinaryExpr(self, expr: n.BinaryExpr) -> str:
        left = self.visit(expr.left)
        right = self.visit(expr.right)
        op = "==" if expr.operator == "==" else expr.operator
        return f"{left} {op} {right}"

    def visit_Literal(self, expr: n.Literal) -> str:
        if expr.literal_kind == "number":
            return _format_number(expr.value)
        if expr.literal_kind == "string":
            return f'"{expr.value}"'
        if expr.literal_kind == "boolean":
            return "true" if expr.value else "false"
        if expr.literal_kind == "vector3":
            x, y, z = expr.value
            return f"Vector3.new({_format_number(x)}, {_format_number(y)}, {_format_number(z)})"
        if expr.literal_kind in ("colorname", "hexcolor"):
            return self._emit_color(expr)
        raise ValueError(f"literal_kind desconocido: {expr.literal_kind}")

    def visit_Identifier(self, expr: n.Identifier) -> str:
        if self._is_property_ref(expr.name):
            return f'self:GetAttribute("{expr.name}")'
        return expr.name

    def _is_property_ref(self, name: str) -> bool:
        """
        Un identificador se resuelve como property_decl (Attribute) si:
        - NO es un parametro local del evento actual (ej. 'amount', 'source'), Y
        - SI corresponde a una propiedad declarada (propia o heredada) de la
          entidad que se esta emitiendo actualmente.
        """
        if name in self._local_names:
            return False
        if self._current_entity is None:
            return False
        return self.resolver.is_property(self._current_entity, name)

    def visit_SelfRef(self, expr: n.SelfRef) -> str:
        return "self"

    def visit_PlayerRef(self, expr: n.PlayerRef) -> str:
        return "player"

    def visit_MemberAccess(self, expr: n.MemberAccess) -> str:
        obj = self.visit(expr.obj)
        return f"{obj}.{expr.member}"

    # ---------------- helpers ----------------

    def _indent(self, code: str) -> str:
        return "\n".join(f"{INDENT}{line}" if line.strip() else "" for line in code.splitlines())

    def _emit_comment_if_any(self, node: n.Node) -> str | None:
        if self.preserve_comments and getattr(node, "leading_comment", None):
            return f"-- {node.leading_comment}"
        return None


def _format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def emit_luau(program: n.Program, preserve_comments: bool = False, symbols: SymbolTable | None = None) -> dict[str, str]:
    """Punto de entrada conveniente para CLI/Tests."""
    emitter = LuauEmitter(preserve_comments=preserve_comments, symbols=symbols)
    return emitter.emit_program(program)
