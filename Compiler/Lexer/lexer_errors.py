"""
lexer_errors.py
Excepciones especificas del analisis lexico de EntityScript.

Cada error incluye linea/columna y un mensaje accionable, siguiendo la
filosofia de 'errores como guia', no solo como rechazo.
"""


class LexError(Exception):
    def __init__(self, code: str, message: str, line: int, column: int):
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"[{code}] Linea {line}:{column} -> {message}")


class UnterminatedStringError(LexError):
    def __init__(self, line: int, column: int):
        super().__init__(
            "UnterminatedString",
            "Cadena de texto sin cerrar. Falta un '\"' de cierre.",
            line,
            column,
        )


class UnterminatedBlockCommentError(LexError):
    def __init__(self, line: int, column: int):
        super().__init__(
            "UnterminatedBlockComment",
            'Se esperaba "###" de cierre antes de fin de archivo.',
            line,
            column,
        )


class UnexpectedCharacterError(LexError):
    def __init__(self, char: str, line: int, column: int):
        super().__init__(
            "UnexpectedCharacter",
            f"Caracter inesperado '{char}'. No pertenece a la gramatica de EntityScript.",
            line,
            column,
        )


class ForbiddenAliasError(LexError):
    """
    Enforcement de 'una unica forma de hacer las cosas': palabras que
    parecen sinonimos de una accion reservada disparan un error con sugerencia,
    en vez de ser tratadas silenciosamente como identificadores validos.
    """
    def __init__(self, found: str, suggestion: str, line: int, column: int):
        super().__init__(
            "ForbiddenAlias",
            f'"{found}" no es una accion valida en EntityScript. '
            f'Quisiste decir "{suggestion}"?',
            line,
            column,
        )
