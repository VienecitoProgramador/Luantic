"""
token_types.py
Definicion de todos los tipos de token reconocidos por el Lexer de EntityScript.

Estos tipos son el 'alfabeto' formal que produce el tokenizer y consume el Parser.
Los comentarios SI se tokenizan aqui, pero se filtran antes de llegar al Parser
(ver tokenizer.py -> comment_table).
"""

from enum import Enum, auto


class TokenType(Enum):
    # Palabras clave estructurales
    ENTITY = auto()
    EXTENDS = auto()
    ON = auto()
    IF = auto()
    ELSE = auto()
    REPEAT = auto()
    TIMES = auto()
    EMIT = auto()
    USE = auto()

    # Estructurales nuevas v0.2
    AFTER = auto()
    FOR = auto()
    IN = auto()
    FUNCTION = auto()
    CONST = auto()
    LEADERSTAT = auto()
    SCORE = auto()
    PLAYERS = auto()
    ALL_KW = auto()
    TEAM_KW = auto()

    # Acciones reservadas (action_name en la EBNF)
    DESTROY = auto()
    SPAWN = auto()
    GIVE = auto()
    PLAY = auto()
    WAIT = auto()
    PRINT = auto()

    # Eventos reservados (event_name en la EBNF)
    EVENT_TOUCH = auto()
    EVENT_SPAWN = auto()
    EVENT_DESTROY = auto()
    EVENT_CLICK = auto()
    EVENT_DAMAGE = auto()
    EVENT_INTERACT = auto()
    EVENT_TIMER = auto()

    # Tipos (type_annotation)
    TYPE_NUMBER = auto()
    TYPE_STRING = auto()
    TYPE_BOOL = auto()
    TYPE_VECTOR3 = auto()
    TYPE_COLOR = auto()
    TYPE_MODEL = auto()
    TYPE_SOUND = auto()

    # Literales
    NUMBER = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()

    # Identificadores y referencias especiales
    IDENTIFIER = auto()
    SELF = auto()
    PLAYER_KW = auto()

    # Operadores
    ASSIGN = auto()          # =
    PLUS_ASSIGN = auto()     # +=
    MINUS_ASSIGN = auto()    # -=
    STAR_ASSIGN = auto()     # *=
    SLASH_ASSIGN = auto()    # /=
    PLUS = auto()            # +
    MINUS = auto()           # -
    AND = auto()
    OR = auto()
    EQ = auto()              # ==
    NEQ = auto()             # !=
    GT = auto()              # >
    LT = auto()              # <
    GTE = auto()             # >=
    LTE = auto()             # <=
    DOT = auto()             # .

    # Delimitadores
    LBRACE = auto()          # {
    RBRACE = auto()          # }
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    COMMA = auto()           # ,
    COLON = auto()           # :
    AT = auto()              # @  (tag_decl)

    # Comentarios (filtrados antes del Parser, ver comment_table)
    LINE_COMMENT = auto()
    BLOCK_COMMENT = auto()

    NEWLINE = auto()
    EOF = auto()


# Palabras reservadas de estructura general
KEYWORDS = {
    "entity": TokenType.ENTITY,
    "extends": TokenType.EXTENDS,
    "on": TokenType.ON,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "repeat": TokenType.REPEAT,
    "times": TokenType.TIMES,
    "emit": TokenType.EMIT,
    "use": TokenType.USE,
    "after": TokenType.AFTER,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "function": TokenType.FUNCTION,
    "const": TokenType.CONST,
    "leaderstat": TokenType.LEADERSTAT,
    "score": TokenType.SCORE,
    "players": TokenType.PLAYERS,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "self": TokenType.SELF,
    "player": TokenType.PLAYER_KW,
    "all": TokenType.ALL_KW,
    "team": TokenType.TEAM_KW,
}

# Acciones reservadas (action_name) -- v0.1 + v0.2
ACTIONS = {
    "destroy": TokenType.DESTROY,
    "spawn": TokenType.SPAWN,
    "give": TokenType.GIVE,
    "play": TokenType.PLAY,
    "wait": TokenType.WAIT,
    "print": TokenType.PRINT,
}

# Eventos reservados (event_name)
EVENTS = {
    "touch": TokenType.EVENT_TOUCH,
    "spawn": TokenType.EVENT_SPAWN,
    "destroy": TokenType.EVENT_DESTROY,
    "click": TokenType.EVENT_CLICK,
    "damage": TokenType.EVENT_DAMAGE,
    "interact": TokenType.EVENT_INTERACT,
    "timer": TokenType.EVENT_TIMER,
}

# Tipos reservados (type_annotation)
TYPES = {
    "Number": TokenType.TYPE_NUMBER,
    "String": TokenType.TYPE_STRING,
    "Bool": TokenType.TYPE_BOOL,
    "Vector3": TokenType.TYPE_VECTOR3,
    "Color": TokenType.TYPE_COLOR,
    "Model": TokenType.TYPE_MODEL,
    "Sound": TokenType.TYPE_SOUND,
}


class Token:
    __slots__ = ("type", "lexeme", "literal", "line", "column")

    def __init__(self, type_: TokenType, lexeme: str, literal, line: int, column: int):
        self.type = type_
        self.lexeme = lexeme
        self.literal = literal
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {self.lexeme!r}, line={self.line})"
