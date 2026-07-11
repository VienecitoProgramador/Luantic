"""
test_semantic.py
Pruebas de la capa semantica: type_checker (herencia valida, propiedades
indefinidas, entidades duplicadas) y comment_linter (warnings no bloqueantes).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Parser.grammar_rules import parse_tokens
from Compiler.Semantic.type_checker import check_program
from Compiler.Semantic.semantic_errors import (
    UndefinedParentEntityError,
    UndefinedPropertyError,
    DuplicateEntityError,
)
from Compiler.Semantic.comment_linter import lint_comments


def _parse(src):
    tokens, comments = tokenize_source(src)
    return parse_tokens(tokens, comments)


def test_valid_inheritance_passes():
    src = '''
entity Character {
    health: Number = 100
}
entity Goblin extends Character {
    on damage(amount) {
        health -= amount
    }
}
'''
    program = _parse(src)
    symbols = check_program(program)
    assert symbols.entity_exists("Goblin")
    assert symbols.resolve_property_type("Goblin", "health") == "Number"


def test_undefined_parent_raises():
    src = 'entity Goblin extends Ghost {\n    health: Number = 10\n}\n'
    program = _parse(src)
    with pytest.raises(UndefinedParentEntityError):
        check_program(program)


def test_undefined_property_in_assignment_raises():
    src = '''
entity Goblin {
    on damage(amount) {
        mana -= amount
    }
}
'''
    program = _parse(src)
    with pytest.raises(UndefinedPropertyError):
        check_program(program)


def test_duplicate_entity_raises():
    src = 'entity Coin {\n    points: Number = 10\n}\nentity Coin {\n    points: Number = 5\n}\n'
    program = _parse(src)
    with pytest.raises(DuplicateEntityError):
        check_program(program)


def test_event_param_assignment_does_not_require_property():
    """Un parametro de evento (ej. `amount`) puede usarse libremente sin
    necesidad de que exista como property_decl de la entidad."""
    src = '''
entity Logger {
    on damage(amount) {
        amount = amount
    }
}
'''
    program = _parse(src)
    check_program(program)  # no debe lanzar


def test_redundant_comment_triggers_warning():
    src = '''
entity Coin {
    on touch(player) {
        # destroy self
        destroy self
    }
}
'''
    program = _parse(src)
    check_program(program)
    warnings = lint_comments(program)
    assert len(warnings) >= 1


def test_contextual_comment_does_not_trigger_warning():
    src = '''
entity Coin {
    # Diseño pidio x2 puntos en fin de semana para retencion
    points: Number = 10
}
'''
    program = _parse(src)
    check_program(program)
    warnings = lint_comments(program)
    assert len(warnings) == 0
