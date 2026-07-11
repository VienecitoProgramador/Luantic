"""
semantic_errors.py
Excepciones de la fase de analisis semantico (post-parseo).
Estas se disparan cuando la sintaxis es valida pero el significado no lo es
(ej. herencia de una entidad inexistente, uso de una propiedad no declarada).
"""


class SemanticError(Exception):
    def __init__(self, code: str, message: str, line: int):
        self.code = code
        self.message = message
        self.line = line
        super().__init__(f"[{code}] Linea {line} -> {message}")


class UndefinedParentEntityError(SemanticError):
    def __init__(self, child: str, parent: str, line: int):
        super().__init__(
            "UndefinedParentEntity",
            f'"{child}" extiende de "{parent}", pero "{parent}" no esta declarada '
            f"en este archivo ni importada.",
            line,
        )


class UndefinedPropertyError(SemanticError):
    def __init__(self, entity: str, prop: str, line: int):
        super().__init__(
            "UndefinedProperty",
            f'La entidad "{entity}" no tiene una propiedad "{prop}" declarada '
            f"(ni heredada), pero se usa en un evento.",
            line,
        )


class DuplicateEntityError(SemanticError):
    def __init__(self, name: str, line: int):
        super().__init__(
            "DuplicateEntity",
            f'Ya existe una entidad llamada "{name}" en este archivo.',
            line,
        )


class ConstReassignmentError(SemanticError):
    def __init__(self, name: str, line: int):
        super().__init__(
            "ConstReassignment",
            f'"{name}" es una constante ("const {name}") y no puede reasignarse.',
            line,
        )


class UndefinedLeaderstatError(SemanticError):
    def __init__(self, leaderstat_name: str, line: int):
        super().__init__(
            "UndefinedLeaderstat",
            f'"score = {leaderstat_name}" referencia un leaderstat que no existe. '
            f'Declaralo con "leaderstat {leaderstat_name} = 0" al inicio del archivo.',
            line,
        )


class UndefinedFunctionError(SemanticError):
    def __init__(self, entity: str, func_name: str, line: int):
        super().__init__(
            "UndefinedFunction",
            f'"{func_name}(...)" no es una funcion declarada en "{entity}". '
            f'Declarala con "function {func_name}(...) {{ ... }}".',
            line,
        )
