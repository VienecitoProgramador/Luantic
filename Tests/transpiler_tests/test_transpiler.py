"""
test_transpiler.py
Pruebas del Transpiler: verifica que construcciones ES especificas produzcan
fragmentos Luau exactos (estilo golden-file, pero inline para legibilidad).

Estas pruebas tambien sirven como documentacion viva de la tabla de
traduccion descrita en el design doc, seccion 4.3.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Parser.grammar_rules import parse_tokens
from Compiler.Semantic.type_checker import check_program
from Compiler.Transpiler.luau_emitter import emit_luau


def _compile(src):
    tokens, comments = tokenize_source(src)
    program = parse_tokens(tokens, comments)
    symbols = check_program(program)
    return emit_luau(program, symbols=symbols)


def test_destroy_self_translates_to_method_call():
    src = 'entity Coin {\n    on touch(player) {\n        destroy self\n    }\n}\n'
    out = _compile(src)["Coin"]
    assert "self:Destroy()" in out


def test_give_translates_to_score_modification():
    src = 'entity Coin {\n    points: Number = 10\n    on touch(player) {\n        give player points\n    }\n}\n'
    out = _compile(src)["Coin"]
    assert 'es_modify_score(self, player, (self:GetAttribute("points")))' in out


def test_property_becomes_attribute_not_local():
    src = 'entity Coin {\n    points: Number = 10\n}\n'
    out = _compile(src)["Coin"]
    assert 'self:SetAttribute("points", 10)' in out
    assert "local points" not in out


def test_compound_assignment_expands_to_valid_luau():
    src = '''
entity Goblin {
    health: Number = 100
    on damage(amount) {
        health -= amount
    }
}
'''
    out = _compile(src)["Goblin"]
    assert '-=' not in out
    assert 'self:SetAttribute("health", self:GetAttribute("health") - amount)' in out


def test_event_wraps_with_dispatcher_call():
    src = 'entity Coin {\n    on touch(player) {\n        destroy self\n    }\n}\n'
    out = _compile(src)["Coin"]
    assert "es_on_touch(self, function(player)" in out
    assert out.strip().endswith("end)")


def test_repeat_loop_translates_to_numeric_for():
    src = '''
entity NPC {
    on timer(seconds) {
        repeat 2 times {
            wait 1
        }
    }
}
'''
    out = _compile(src)["NPC"]
    assert "for _es_i = 1, 2 do" in out
    assert "end" in out


def test_conditional_translates_to_if_then_end():
    src = '''
entity Goblin {
    health: Number = 100
    on damage(amount) {
        if health <= 0 {
            destroy self
        }
    }
}
'''
    out = _compile(src)["Goblin"]
    assert 'if self:GetAttribute("health") <= 0 then' in out
    assert out.count("end") >= 2  # cierre del if + cierre del function


def test_inherited_property_resolved_via_attribute_across_entities():
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
    out = _compile(src)["Goblin"]
    assert 'self:GetAttribute("health")' in out
    assert 'es_inherit(self, "Character")' in out


def test_event_param_is_not_treated_as_property():
    src = '''
entity Goblin {
    on damage(amount, source) {
        print amount
    }
}
'''
    out = _compile(src)["Goblin"]
    assert 'GetAttribute("amount")' not in out
    assert "print(amount)" in out


def test_vector3_literal_translates_to_vector3_new():
    src = 'entity Spawner {\n    origin: Vector3 = (0, 10, 0)\n}\n'
    out = _compile(src)["Spawner"]
    assert 'self:SetAttribute("origin", Vector3.new(0, 10, 0))' in out


def test_member_access_on_player_translates_directly():
    src = '''
entity Door {
    on interact(player) {
        if player.isAdmin {
            give player 1000
        } else {
            give player 10
        }
    }
}
'''
    out = _compile(src)["Door"]
    assert "if player.isAdmin then" in out
    assert 'es_modify_score(self, player, (1000))' in out
    assert 'es_modify_score(self, player, (10))' in out
