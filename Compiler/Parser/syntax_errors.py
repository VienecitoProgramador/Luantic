"""
syntax_errors.py
Excepciones especificas del analisis sintactico de EntityScript.

Cada error de esta capa corresponde a una violacion de la EBNF formal
del design doc, o a una regla de "una unica forma de hacer las cosas"
que se detecta a nivel de estructura (no de lexico).
"""


class ParseError(Exception):
    def __init__(self, code: str, message: str, line: int):
        self.code = code
        self.message = message
        self.line = line
        super().__init__(f"[{code}] Linea {line} -> {message}")


class UnexpectedTokenError(ParseError):
    def __init__(self, found: str, expected: str, line: int):
        super().__init__(
            "UnexpectedToken",
            f'Se encontro "{found}" pero se esperaba {expected}.',
            line,
        )


class EntityNameCaseError(ParseError):
    def __init__(self, found: str, line: int):
        suggestion = found[0].upper() + found[1:] if found else found
        super().__init__(
            "EntityNameMustBePascalCase",
            f'"{found}" debe empezar en mayuscula ("{suggestion}").',
            line,
        )


class UnknownEventError(ParseError):
    def __init__(self, found: str, suggestion: str, line: int):
        msg = f'"{found}" no existe.'
        if suggestion:
            msg += f' Quisiste decir "{suggestion}"? (case-sensitive)'
        super().__init__("UnknownEvent", msg, line)


class UnknownTagError(ParseError):
    def __init__(self, found: str, line: int):
        super().__init__(
            "UnknownTag",
            f'"@{found}" no existe. Los tags son camelCase (ej. "@locked").',
            line,
        )


class UnsupportedOperatorError(ParseError):
    def __init__(self, found: str, line: int):
        super().__init__(
            "UnsupportedOperator",
            f'"{found}" no esta definido en EntityScript.',
            line,
        )


class GlobalEventOnNonGlobalEntityError(ParseError):
    def __init__(self, event_name: str, entity_name: str, line: int):
        super().__init__(
            "GlobalEventOnNonGlobalEntity",
            f'El evento "on {event_name}" solo es valido en entidades con el tag "@global" '
            f'(representan logica de servidor, no objetos fisicos). Agrega "@global" a '
            f'"{entity_name}" o usa otro evento.',
            line,
        )
