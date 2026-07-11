"""
type_checker.py
Analisis semantico de EntityScript: valida el AST DESPUES de que el Parser
confirmo que es sintacticamente correcto.

Responsabilidades:
1. Detectar entidades duplicadas.
2. Validar que `extends` apunte a una entidad existente.
3. Validar que las variables usadas en asignaciones dentro de eventos/funciones
   correspondan a propiedades declaradas (o heredadas) de la entidad.
4. (v0.2) Validar que no se reasigne una `const`.
5. (v0.2) Validar que `score = X` referencie un `leaderstat` declarado.
6. (v0.2) Validar que las llamadas a funciones (`Nombre(args)`) referencien
   una `function` declarada en la misma entidad.

No se encarga de generar codigo (eso es Transpiler/). Su unica salida es:
lanzar una excepcion semantic_errors.* o no lanzar nada (AST valido).
"""

from ..AST import nodes as n
from ..AST.visitor import ASTVisitor
from .symbol_table import SymbolTable
from .semantic_errors import (
    UndefinedParentEntityError,
    UndefinedPropertyError,
    DuplicateEntityError,
    ConstReassignmentError,
    UndefinedLeaderstatError,
    UndefinedFunctionError,
)


class TypeChecker(ASTVisitor):
    def __init__(self):
        self.symbols = SymbolTable()

    def check(self, program: n.Program) -> SymbolTable:
        self.symbols.register_leaderstats(program)

        seen_names = set()
        for entity in program.entities:
            if entity.name in seen_names:
                raise DuplicateEntityError(entity.name, entity.line)
            seen_names.add(entity.name)
            self.symbols.register_entity(entity)

        for entity in program.entities:
            self._check_entity(entity)

        return self.symbols

    def _check_entity(self, entity: n.EntityDecl):
        if entity.parent and not self.symbols.entity_exists(entity.parent):
            raise UndefinedParentEntityError(entity.name, entity.parent, entity.line)

        if entity.score_binding and not self.symbols.leaderstat_exists(entity.score_binding.leaderstat_name):
            raise UndefinedLeaderstatError(entity.score_binding.leaderstat_name, entity.score_binding.line)

        function_names = {f.name for f in entity.functions}

        for fn in entity.functions:
            self._check_statement_list(entity, fn.body, set(fn.params), function_names)

        for event in entity.events:
            self._check_statement_list(entity, event.body, set(event.params), function_names)

    def _check_statement_list(self, entity: n.EntityDecl, statements: list, local_names: set, function_names: set):
        for stmt in statements:
            self._check_statement(entity, stmt, local_names, function_names)

    def _check_statement(self, entity: n.EntityDecl, stmt: n.Stmt, local_names: set, function_names: set):
        if isinstance(stmt, n.Assignment):
            if self.symbols.is_const(entity.name, stmt.target):
                raise ConstReassignmentError(stmt.target, stmt.line)
            if stmt.target not in local_names:
                resolved = self.symbols.resolve_property_type(entity.name, stmt.target)
                if resolved is None:
                    raise UndefinedPropertyError(entity.name, stmt.target, stmt.line)
        elif isinstance(stmt, n.Conditional):
            self._check_statement_list(entity, stmt.then_branch, local_names, function_names)
            if stmt.else_branch:
                self._check_statement_list(entity, stmt.else_branch, local_names, function_names)
        elif isinstance(stmt, n.Loop):
            self._check_statement_list(entity, stmt.body, local_names, function_names)
        elif isinstance(stmt, n.AfterStmt):
            self._check_statement_list(entity, stmt.body, local_names, function_names)
        elif isinstance(stmt, n.ForStmt):
            inner_locals = local_names | {stmt.var_name}
            self._check_statement_list(entity, stmt.body, inner_locals, function_names)
        elif isinstance(stmt, n.FunctionCall):
            if stmt.name not in function_names:
                raise UndefinedFunctionError(entity.name, stmt.name, stmt.line)
        # ActionCall y EmitStmt no requieren chequeo adicional en v0.2


def check_program(program: n.Program) -> SymbolTable:
    return TypeChecker().check(program)
