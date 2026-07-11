"""
symbol_table.py
Tabla de simbolos de EntityScript: registra entidades declaradas, sus
propiedades y su jerarquia de herencia (`extends`).

Usada por:
- type_checker.py, para validar que `extends` referencia una entidad existente
  y que las propiedades usadas en eventos existen.
- Editor/lsp, para autocompletado (reutiliza esta misma clase).
"""

from dataclasses import dataclass, field
from ..AST import nodes as n


@dataclass
class EntitySymbol:
    name: str
    parent: str | None
    properties: dict[str, str] = field(default_factory=dict)  # nombre -> type_annotation
    consts: set[str] = field(default_factory=set)
    line: int = 0


class SymbolTable:
    def __init__(self):
        self.entities: dict[str, EntitySymbol] = {}
        self.leaderstats: set[str] = set()

    def register_entity(self, entity: n.EntityDecl):
        props = {p.name: p.type_annotation for p in entity.properties}
        consts = {c.name for c in entity.consts}
        self.entities[entity.name] = EntitySymbol(
            name=entity.name, parent=entity.parent, properties=props, consts=consts, line=entity.line
        )

    def register_leaderstats(self, program: n.Program):
        for ls in program.leaderstats:
            self.leaderstats.add(ls.name)

    def resolve_property_type(self, entity_name: str, prop_name: str) -> str | None:
        """Busca el tipo de una propiedad recorriendo la cadena de `extends`."""
        current = self.entities.get(entity_name)
        visited = set()
        while current is not None and current.name not in visited:
            visited.add(current.name)
            if prop_name in current.properties:
                return current.properties[prop_name]
            current = self.entities.get(current.parent) if current.parent else None
        return None

    def is_const(self, entity_name: str, name: str) -> bool:
        """Busca si `name` es una constante, recorriendo la cadena de `extends`."""
        current = self.entities.get(entity_name)
        visited = set()
        while current is not None and current.name not in visited:
            visited.add(current.name)
            if name in current.consts:
                return True
            current = self.entities.get(current.parent) if current.parent else None
        return False

    def leaderstat_exists(self, name: str) -> bool:
        return name in self.leaderstats

    def entity_exists(self, name: str) -> bool:
        return name in self.entities

    def build_from_program(self, program: n.Program) -> "SymbolTable":
        self.register_leaderstats(program)
        for entity in program.entities:
            self.register_entity(entity)
        return self
