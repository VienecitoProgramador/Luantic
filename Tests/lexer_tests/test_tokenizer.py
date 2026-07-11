"""
test_tokenizer.py
Pruebas del Lexer: tokens correctos, comentarios filtrados a comment_table,
y errores lexicos (alias prohibidos, strings/bloques sin cerrar).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Lexer.token_types import TokenType
from Compiler.Lexer.lexer_errors import (
    UnterminatedStringError,
    UnterminatedBlockCommentError,
    ForbiddenAliasError,
    UnexpectedCharacterError,
)


def _types(tokens):
    return [t.type for t in tokens]


def test_basic_entity_tokens():
    src = 'entity Coin {\n    points: Number = 10\n}\n'
    tokens, comments = tokenize_source(src)
    assert TokenType.ENTITY in _types(tokens)
    assert TokenType.IDENTIFIER in _types(tokens)
    assert TokenType.COLON in _types(tokens)
    assert TokenType.TYPE_NUMBER in _types(tokens)
    assert comments == []


def test_line_comment_goes_to_comment_table_not_tokens():
    src = '# esto es un comentario\nentity Coin {\n}\n'
    tokens, comments = tokenize_source(src)
    assert TokenType.LINE_COMMENT not in _types(tokens)
    assert len(comments) == 1
    assert comments[0]["text"] == "esto es un comentario"
    assert comments[0]["kind"] == "line"


def test_block_comment_goes_to_comment_table():
    src = '###\nlinea uno\nlinea dos\n###\nentity Coin {}\n'
    tokens, comments = tokenize_source(src)
    assert len(comments) == 1
    assert comments[0]["kind"] == "block"
    assert "linea uno" in comments[0]["text"]


def test_unterminated_block_comment_raises():
    src = '### nunca se cierra\nentity Coin {}\n'
    with pytest.raises(UnterminatedBlockCommentError):
        tokenize_source(src)


def test_unterminated_string_raises():
    src = 'entity Coin { name: String = "sin cerrar\n}'
    with pytest.raises(UnterminatedStringError):
        tokenize_source(src)


@pytest.mark.parametrize("alias", ["remove", "delete", "kill"])
def test_forbidden_action_alias_raises(alias):
    src = f'on touch(player) {{\n    {alias} self\n}}\n'
    with pytest.raises(ForbiddenAliasError):
        tokenize_source(src)


def test_compound_operators_tokenize_correctly():
    src = 'health -= 10\nscore += 5\n'
    tokens, _ = tokenize_source(src)
    types = _types(tokens)
    assert TokenType.MINUS_ASSIGN in types
    assert TokenType.PLUS_ASSIGN in types


def test_lua_style_comment_is_rejected():
    src = "-- esto es Lua, no EntityScript\n"
    with pytest.raises(UnexpectedCharacterError):
        tokenize_source(src)


def test_vector3_and_number_literals():
    src = "position: Vector3 = (1, 2, 3)\n"
    tokens, _ = tokenize_source(src)
    numbers = [t for t in tokens if t.type == TokenType.NUMBER]
    assert len(numbers) == 3
    assert [n.literal for n in numbers] == [1.0, 2.0, 3.0]
