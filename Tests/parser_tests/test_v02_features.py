"""
test_v02_features.py
Pruebas de las features nuevas de v0.2: leaderstats, score binding, const,
function/function_call, propiedades fisicas, colores, after, for players,
eventos @global, y operadores *=//=.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Parser.grammar_rules import parse_tokens
from Compiler.Parser.syntax_errors import GlobalEventOnNonGlobalEntityError
from Compiler.Semantic.type_checker import check_program
from Compiler.Semantic.semantic_errors import (
    ConstReassignmentError,
    UndefinedLeaderstatError,
    UndefinedFunctionError,
)
from Compiler.Transpiler.luau_emitter import emit_luau
from Compiler.Transpiler.leaderstats_emitter import emit_leaderstats_script
from Compiler.AST import nodes as n


def _parse(src):
    tokens, comments = tokenize_source(src)
    return parse_tokens(tokens, comments)


def _compile(src):
    program = _parse(src)
    symbols = check_program(program)
    return emit_luau(program, symbols=symbols), program


# ---------------- Parser: features nuevas ----------------

def test_leaderstat_decl_parses_at_top_level():
    program = _parse("leaderstat Coins = 0\n\nentity Coin {\n    value = 1\n}\n")
    assert len(program.leaderstats) == 1
    assert program.leaderstats[0].name == "Coins"
    assert program.leaderstats[0].initial == 0.0


def test_property_infers_type_from_literal():
    program = _parse("entity Coin {\n    value = 10\n}\n")
    prop = program.entities[0].properties[0]
    assert prop.type_annotation == "Number"


def test_const_decl_parses():
    program = _parse("entity Coin {\n    const Max = 100\n}\n")
    assert program.entities[0].consts[0].name == "Max"


def test_score_binding_parses():
    program = _parse("entity Coin {\n    score = Coins\n}\n")
    assert program.entities[0].score_binding.leaderstat_name == "Coins"


def test_physical_properties_parse():
    src = 'entity Coin {\n    position = (0, 5, 0)\n    color = red\n    anchored = true\n}\n'
    program = _parse(src)
    names = [pp.name for pp in program.entities[0].physical_props]
    assert names == ["position", "color", "anchored"]


def test_hex_color_recognized_as_hexcolor_literal():
    program = _parse('entity Coin {\n    color = "#FF00AA"\n}\n')
    pp = program.entities[0].physical_props[0]
    assert pp.value.literal_kind == "hexcolor"


def test_function_decl_and_call_parse():
    src = '''
entity Coin {
    function Collect(player) {
        destroy self
    }
    on touch(player) {
        Collect(player)
    }
}
'''
    program = _parse(src)
    entity = program.entities[0]
    assert entity.functions[0].name == "Collect"
    call = entity.events[0].body[0]
    assert isinstance(call, n.FunctionCall)
    assert call.name == "Collect"


def test_after_stmt_parses():
    src = 'entity Coin {\n    on touch(player) {\n        after 2 {\n            destroy self\n        }\n    }\n}\n'
    program = _parse(src)
    stmt = program.entities[0].events[0].body[0]
    assert isinstance(stmt, n.AfterStmt)


def test_for_players_parses():
    src = '''
entity GameManager {
    @global
    on timer(seconds) {
        for player in players {
            message player "hola"
        }
    }
}
'''
    program = _parse(src)
    stmt = program.entities[0].events[0].body[0]
    assert isinstance(stmt, n.ForStmt)
    assert stmt.var_name == "player"
    assert stmt.collection == "players"


def test_star_and_slash_assign_operators_parse():
    src = 'entity Coin {\n    value = 10\n    on touch(player) {\n        value *= 2\n        value /= 2\n    }\n}\n'
    program = _parse(src)
    stmts = program.entities[0].events[0].body
    assert stmts[0].operator == "*="
    assert stmts[1].operator == "/="


def test_global_event_on_non_global_entity_raises():
    src = 'entity Coin {\n    on join(player) {\n        print player\n    }\n}\n'
    with pytest.raises(GlobalEventOnNonGlobalEntityError):
        _parse(src)


def test_global_event_on_global_entity_succeeds():
    src = 'entity GameManager {\n    @global\n    on join(player) {\n        print player\n    }\n}\n'
    program = _parse(src)  # no debe lanzar
    assert program.entities[0].events[0].event_name == "join"


def test_message_all_parses():
    src = 'entity GameManager {\n    @global\n    on join(player) {\n        message all "hola a todos"\n    }\n}\n'
    program = _parse(src)
    call = program.entities[0].events[0].body[0]
    assert call.args[0].value == "all"


def test_message_team_parses():
    src = 'entity GameManager {\n    @global\n    on join(player) {\n        message team Red "vamos equipo"\n    }\n}\n'
    program = _parse(src)
    call = program.entities[0].events[0].body[0]
    assert call.args[0].value == "team:Red"


# ---------------- Semantic: validaciones nuevas ----------------

def test_const_reassignment_raises():
    src = 'entity Coin {\n    const Max = 100\n    on touch(player) {\n        Max = 50\n    }\n}\n'
    program = _parse(src)
    with pytest.raises(ConstReassignmentError):
        check_program(program)


def test_undefined_leaderstat_raises():
    src = 'entity Coin {\n    score = Coins\n    on touch(player) {\n        give player 10\n    }\n}\n'
    program = _parse(src)
    with pytest.raises(UndefinedLeaderstatError):
        check_program(program)


def test_defined_leaderstat_passes():
    src = 'leaderstat Coins = 0\n\nentity Coin {\n    score = Coins\n    on touch(player) {\n        give player 10\n    }\n}\n'
    program = _parse(src)
    check_program(program)  # no debe lanzar


def test_undefined_function_call_raises():
    src = 'entity Coin {\n    on touch(player) {\n        Collect(player)\n    }\n}\n'
    program = _parse(src)
    with pytest.raises(UndefinedFunctionError):
        check_program(program)


def test_defined_function_call_passes():
    src = '''
entity Coin {
    function Collect(player) {
        destroy self
    }
    on touch(player) {
        Collect(player)
    }
}
'''
    program = _parse(src)
    check_program(program)  # no debe lanzar


# ---------------- Transpiler: emision correcta ----------------

def test_const_emits_as_local_not_attribute():
    out, _ = _compile('entity Coin {\n    const Max = 100\n}\n')
    assert "local Max = 100" in out["Coin"]
    assert 'SetAttribute("Max"' not in out["Coin"]


def test_score_binding_emits_score_target_attribute():
    src = 'leaderstat Coins = 0\n\nentity Coin {\n    score = Coins\n}\n'
    out, _ = _compile(src)
    assert 'self:SetAttribute("ESScoreTarget", "Coins")' in out["Coin"]


def test_give_uses_es_modify_score():
    src = 'leaderstat Coins = 0\n\nentity Coin {\n    score = Coins\n    on touch(player) {\n        give player 10\n    }\n}\n'
    out, _ = _compile(src)
    assert "es_modify_score(self, player, (10))" in out["Coin"]


def test_take_uses_negative_amount():
    src = 'leaderstat Coins = 0\n\nentity Coin {\n    score = Coins\n    on touch(player) {\n        take player 5\n    }\n}\n'
    out, _ = _compile(src)
    assert "es_modify_score(self, player, -(5))" in out["Coin"]


def test_function_emits_local_function():
    src = '''
entity Coin {
    function Collect(player) {
        destroy self
    }
    on touch(player) {
        Collect(player)
    }
}
'''
    out, _ = _compile(src)
    assert "local function Collect(player)" in out["Coin"]
    assert "Collect(player)" in out["Coin"]


def test_physical_property_color_name_emits_rgb():
    out, _ = _compile('entity Coin {\n    color = red\n}\n')
    assert "self.Color = Color3.fromRGB(255, 0, 0)" in out["Coin"]


def test_physical_property_hex_color_emits_rgb():
    out, _ = _compile('entity Coin {\n    color = "#FFD700"\n}\n')
    assert "self.Color = Color3.fromRGB(255, 215, 0)" in out["Coin"]


def test_after_emits_task_delay():
    src = 'entity Coin {\n    on touch(player) {\n        after 2 {\n            destroy self\n        }\n    }\n}\n'
    out, _ = _compile(src)
    assert "task.delay(2, function()" in out["Coin"]


def test_for_players_emits_ipairs_getplayers():
    src = '''
entity GameManager {
    @global
    on timer(seconds) {
        for player in players {
            message player "hola"
        }
    }
}
'''
    out, _ = _compile(src)
    assert 'for _, player in ipairs(game:GetService("Players"):GetPlayers()) do' in out["GameManager"]


def test_star_slash_assign_expand_correctly():
    src = 'entity Coin {\n    value = 10\n    on touch(player) {\n        value *= 2\n        value /= 2\n    }\n}\n'
    out, _ = _compile(src)
    assert 'self:SetAttribute("value", self:GetAttribute("value") * 2)' in out["Coin"]
    assert 'self:SetAttribute("value", self:GetAttribute("value") / 2)' in out["Coin"]


def test_leaderstats_script_generation():
    program = _parse("leaderstat Coins = 0\nleaderstat Wins = 0\n\nentity Foo {\n    value = 1\n}\n")
    script = emit_leaderstats_script(program.leaderstats)
    assert script is not None
    assert 'Instance.new("IntValue")' in script
    assert "Coins.Name = \"Coins\"" in script
    assert "Wins.Name = \"Wins\"" in script


def test_no_leaderstats_returns_none():
    program = _parse("entity Foo {\n    value = 1\n}\n")
    script = emit_leaderstats_script(program.leaderstats)
    assert script is None


def test_negative_number_literal_parses():
    """Bug real: `value = -10` fallaba con UnexpectedToken antes del fix."""
    program = _parse("entity Coin {\n    penalty = -10\n}\n")
    prop = program.entities[0].properties[0]
    assert prop.default_value.value == -10.0


def test_negative_number_in_vector3_parses():
    """Bug real: `position = (0, -5, 0)` fallaba antes del fix."""
    program = _parse("entity Coin {\n    position = (0, -5, 0)\n}\n")
    pp = program.entities[0].physical_props[0]
    assert pp.value.value == (0.0, -5.0, 0.0)


def test_negative_number_emits_correctly_in_luau():
    out, _ = _compile("entity Coin {\n    penalty = -10\n    position = (0, -5, 0)\n}\n")
    assert 'self:SetAttribute("penalty", -10)' in out["Coin"]
    assert "Vector3.new(0, -5, 0)" in out["Coin"]


def test_interval_tag_configures_timer_attribute():
    """
    Bug real: antes no existia forma de configurar el intervalo de
    `on timer`, siempre quedaba fijo en 1 segundo (default del Runtime).
    @interval(N) permite configurarlo desde EntityScript.
    """
    src = 'entity NPC {\n    @interval(5)\n    on timer(seconds) {\n        print "tick"\n    }\n}\n'
    out, _ = _compile(src)
    assert 'self:SetAttribute("ESTimerInterval", 5)' in out["NPC"]
