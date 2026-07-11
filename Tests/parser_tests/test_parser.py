"""
test_parser.py
Pruebas del Parser: construccion correcta del AST y errores sintacticos
(nombre de entidad no-PascalCase, evento desconocido, operador no soportado).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Parser.grammar_rules import parse_tokens
from Compiler.Parser.syntax_errors import (
    EntityNameCaseError,
    UnknownEventError,
    UnexpectedTokenError,
)
from Compiler.AST import nodes as n


def _parse(src):
    tokens, comments = tokenize_source(src)
    return parse_tokens(tokens, comments)


def test_parses_minimal_entity():
    program = _parse('entity Coin {\n    points: Number = 10\n}\n')
    assert len(program.entities) == 1
    entity = program.entities[0]
    assert entity.name == "Coin"
    assert entity.properties[0].name == "points"
    assert entity.properties[0].default_value.value == 10.0


def test_parses_entity_with_extends():
    program = _parse('entity Goblin extends Character {\n    health: Number = 10\n}\n')
    assert program.entities[0].parent == "Character"


def test_parses_event_with_params_and_body():
    src = '''
entity Coin {
    on touch(player) {
        destroy self
    }
}
'''
    program = _parse(src)
    event = program.entities[0].events[0]
    assert event.event_name == "touch"
    assert event.params == ["player"]
    assert isinstance(event.body[0], n.ActionCall)
    assert event.body[0].action_name == "destroy"


def test_parses_conditional_with_else():
    src = '''
entity Goblin {
    on damage(amount) {
        if health <= 0 {
            destroy self
        } else {
            play "sound"
        }
    }
}
'''
    program = _parse(src)
    stmt = program.entities[0].events[0].body[0]
    assert isinstance(stmt, n.Conditional)
    assert stmt.else_branch is not None


def test_parses_repeat_loop():
    src = '''
entity NPC {
    on timer(seconds) {
        repeat 3 times {
            wait 1
        }
    }
}
'''
    program = _parse(src)
    stmt = program.entities[0].events[0].body[0]
    assert isinstance(stmt, n.Loop)
    assert stmt.count_expr.value == 3.0


def test_entity_name_lowercase_raises():
    with pytest.raises(EntityNameCaseError):
        _parse('entity coin {\n    points: Number = 10\n}\n')


def test_unknown_event_name_raises():
    with pytest.raises(UnknownEventError):
        _parse('entity Coin {\n    on Touch(player) {\n        destroy self\n    }\n}\n')


def test_then_keyword_is_rejected():
    src = '''
entity Goblin {
    on damage(amount) {
        if health <= 0 then {
            destroy self
        }
    }
}
'''
    with pytest.raises(UnexpectedTokenError):
        _parse(src)


def test_comment_attaches_as_leading_comment_to_property():
    src = '# Balance ajustado tras playtest\nentity Coin {\n    points: Number = 10\n}\n'
    program = _parse(src)
    assert program.entities[0].leading_comment == "Balance ajustado tras playtest"


def test_give_action_without_parens_parses_multiple_bare_args():
    src = '''
entity Coin {
    on touch(player) {
        give player points
    }
}
'''
    program = _parse(src)
    call = program.entities[0].events[0].body[0]
    assert isinstance(call, n.ActionCall)
    assert call.action_name == "give"
    assert len(call.args) == 2
