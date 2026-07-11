"""
module_errors.py
Excepciones de la resolucion de `use` (imports entre archivos .es).
"""


class ModuleError(Exception):
    def __init__(self, code: str, message: str, line: int):
        self.code = code
        self.message = message
        self.line = line
        super().__init__(f"[{code}] Linea {line} -> {message}")


class ModuleNotFoundError_(ModuleError):
    def __init__(self, path_str: str, tried_paths: list, line: int):
        tried = ", ".join(tried_paths)
        super().__init__(
            "ModuleNotFound",
            f'No se encontro el modulo "{path_str}". Se busco en: {tried}',
            line,
        )


class CircularImportError(ModuleError):
    def __init__(self, path_str: str, chain: list, line: int):
        chain_str = " -> ".join(chain + [path_str])
        super().__init__(
            "CircularImport",
            f'Importacion circular detectada: {chain_str}',
            line,
        )


class DuplicateEntityAcrossModulesError(ModuleError):
    def __init__(self, entity_name: str, first_file: str, second_file: str, line: int):
        super().__init__(
            "DuplicateEntityAcrossModules",
            f'La entidad "{entity_name}" esta declarada en dos archivos distintos: '
            f'"{first_file}" y "{second_file}". Cada nombre de entidad debe ser unico '
            f'en todo el proyecto, incluso entre archivos importados con "use". '
            f'Renombra una de las dos.',
            line,
        )
