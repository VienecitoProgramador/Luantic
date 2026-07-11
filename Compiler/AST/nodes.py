"""
nodes.py
Definicion de los nodos del Arbol de Sintaxis Abstracta (AST) de EntityScript.

Cada nodo corresponde 1:1 a una regla de la EBNF del documento de diseño.
Los nodos son estructuras de datos puras (dataclasses): no contienen logica
de transpilacion. Esa responsabilidad vive en Compiler/Transpiler/.

Los comentarios NO son nodos del AST (ver design doc, seccion "comment_table").
Se adjuntan como metadata opcional (campo `leading_comment`) a los nodos que
los preceden en el codigo fuente, para que Editor/ y Docs/ puedan usarlos
sin que contaminen la logica semantica del compilador.
"""

from dataclasses import dataclass, field
from typing import Optional, Union


# ==================== Nodo base ====================

@dataclass
class Node:
    line: int = field(default=0, kw_only=True)
    leading_comment: Optional[str] = field(default=None, kw_only=True)


# ==================== Programa ====================

@dataclass
class Program(Node):
    imports: list["ImportDecl"]
    entities: list["EntityDecl"]
    leaderstats: list["LeaderstatDecl"] = field(default_factory=list)


@dataclass
class ImportDecl(Node):
    path: list[str]  # ej. ["Combat", "DamageTypes"]


@dataclass
class LeaderstatDecl(Node):
    name: str
    initial: float


# ==================== Entidades ====================

@dataclass
class EntityDecl(Node):
    name: str
    parent: Optional[str]
    properties: list["PropertyDecl"]
    events: list["EventBlock"]
    tags: list["TagDecl"]
    functions: list["FunctionDecl"] = field(default_factory=list)
    consts: list["ConstDecl"] = field(default_factory=list)
    score_binding: Optional["ScoreBinding"] = None
    physical_props: list["PhysicalProperty"] = field(default_factory=list)


@dataclass
class PropertyDecl(Node):
    name: str
    type_annotation: str
    default_value: "Expr"


@dataclass
class ConstDecl(Node):
    name: str
    value: "Expr"


@dataclass
class ScoreBinding(Node):
    leaderstat_name: str


@dataclass
class PhysicalProperty(Node):
    name: str  # position, rotation, size, color, material, anchored, collision, transparency
    value: "Expr"


@dataclass
class TagDecl(Node):
    name: str
    args: list["Expr"]


@dataclass
class FunctionDecl(Node):
    name: str
    params: list[str]
    body: list["Stmt"]


# ==================== Eventos ====================

@dataclass
class EventBlock(Node):
    event_name: str
    params: list[str]
    body: list["Stmt"]


# ==================== Sentencias (Stmt) ====================

class Stmt(Node):
    pass


@dataclass
class Assignment(Stmt):
    target: str
    operator: str  # "=", "+=", "-="
    value: "Expr"


@dataclass
class ActionCall(Stmt):
    action_name: str
    args: list["Expr"]


@dataclass
class Conditional(Stmt):
    condition: "Expr"
    then_branch: list["Stmt"]
    else_branch: Optional[list["Stmt"]]


@dataclass
class Loop(Stmt):
    count_expr: "Expr"
    body: list["Stmt"]


@dataclass
class EmitStmt(Stmt):
    event_name: str
    args: list["Expr"]


@dataclass
class FunctionCall(Stmt):
    name: str
    args: list["Expr"]


@dataclass
class AfterStmt(Stmt):
    delay_expr: "Expr"
    body: list["Stmt"]


@dataclass
class ForStmt(Stmt):
    var_name: str
    collection: str  # "players" en v0.2, unica coleccion soportada
    body: list["Stmt"]


# ==================== Expresiones (Expr) ====================

class Expr(Node):
    pass


@dataclass
class BinaryExpr(Expr):
    left: "Expr"
    operator: str
    right: "Expr"


@dataclass
class Literal(Expr):
    value: Union[float, str, bool, tuple]
    literal_kind: str  # "number" | "string" | "boolean" | "vector3"


@dataclass
class Identifier(Expr):
    name: str


@dataclass
class SelfRef(Expr):
    pass


@dataclass
class PlayerRef(Expr):
    pass


@dataclass
class MemberAccess(Expr):
    obj: "Expr"
    member: str
