#!/usr/bin/env python3
"""
es_build.py
CLI principal: compila un archivo .es a uno o mas archivos .luau.

Uso:
    python es_build.py <archivo.es> [--out DIR] [--preserve-comments] [--emit-warnings]

Pipeline (refleja exactamente Compiler/ segun el design doc):
    source (.es)
        -> Lexer (tokenizer.py)          => tokens + comment_table
        -> Parser (grammar_rules.py)     => AST (Program)
        -> Semantic (type_checker.py)    => SymbolTable validada
        -> Semantic (comment_linter.py)  => warnings no bloqueantes
        -> Transpiler (luau_emitter.py)  => {nombre_entidad: codigo_luau}
        -> disco (.luau)
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Lexer.lexer_errors import LexError
from Compiler.Parser.grammar_rules import parse_tokens
from Compiler.Parser.syntax_errors import ParseError
from Compiler.Semantic.type_checker import check_program
from Compiler.Semantic.semantic_errors import SemanticError
from Compiler.Semantic.comment_linter import lint_comments
from Compiler.Semantic.module_resolver import resolve_program
from Compiler.Semantic.module_errors import ModuleError
from Compiler.Transpiler.luau_emitter import emit_luau
from Compiler.Transpiler.leaderstats_emitter import emit_leaderstats_script
from CLI.error_reporter import report_error, report_warnings

LUAU_HEADER_TEMPLATE = """--!strict
-- Generado automaticamente por EntityScript v0.2 -- NO EDITAR A MANO.
-- Fuente: {source_name}

local es = require(game:GetService("ReplicatedStorage"):WaitForChild("EntityScriptRuntime"))
local es_give_stat = es.es_give_stat
local es_modify_score = es.es_modify_score
local es_set_score = es.es_set_score
local es_heal = es.es_heal
local es_apply_damage = es.es_apply_damage
local es_teleport = es.es_teleport
local es_message = es.es_message
local es_find = es.es_find
local es_play_sound = es.es_play_sound
local es_spawn = es.es_spawn
local es_wait = es.es_wait
local es_apply_tag = es.es_apply_tag
local es_inherit = es.es_inherit
local es_emit = es.es_emit
local es_on_touch = es.es_on_touch
local es_on_spawn = es.es_on_spawn
local es_on_destroy = es.es_on_destroy
local es_on_click = es.es_on_click
local es_on_damage = es.es_on_damage
local es_on_interact = es.es_on_interact
local es_on_timer = es.es_on_timer
local es_on_join = es.es_on_join
local es_on_leave = es.es_on_leave
local es_on_death = es.es_on_death
local es_on_respawn = es.es_on_respawn

"""


def compile_source(source: str, source_name: str, preserve_comments: bool = False, search_roots=None):
    tokens, comment_table = tokenize_source(source, source_name)
    program = parse_tokens(tokens, comment_table)
    program = resolve_program(program, source_name, search_roots=search_roots)
    symbols = check_program(program)
    warnings = lint_comments(program)
    entities_luau = emit_luau(program, preserve_comments=preserve_comments, symbols=symbols)
    leaderstats_luau = emit_leaderstats_script(program.leaderstats)
    return entities_luau, warnings, leaderstats_luau


def main():
    parser = argparse.ArgumentParser(description="Compila archivos .es a .luau")
    parser.add_argument("source", help="Archivo .es de entrada")
    parser.add_argument("--out", default="./build", help="Directorio de salida")
    parser.add_argument("--preserve-comments", action="store_true",
                         help="Re-emite comentarios de ES como comentarios Luau en el output")
    parser.add_argument("--quiet-warnings", action="store_true",
                         help="Suprime warnings del comment_linter")
    args = parser.parse_args()

    with open(args.source, "r", encoding="utf-8") as f:
        source = f.read()
    source_lines = source.splitlines()

    try:
        entities_luau, warnings, leaderstats_luau = compile_source(
            source, args.source, preserve_comments=args.preserve_comments
        )
    except (LexError, ParseError, SemanticError, ModuleError) as e:
        report_error(source_lines, e)
        sys.exit(1)

    if not args.quiet_warnings:
        report_warnings(warnings)

    os.makedirs(args.out, exist_ok=True)

    if leaderstats_luau:
        ls_path = os.path.join(args.out, "LeaderstatsSetup.luau")
        with open(ls_path, "w", encoding="utf-8") as f:
            f.write(leaderstats_luau)
        print(f"✓ LeaderstatsSetup -> {ls_path}  (pegar en ServerScriptService)")

    for entity_name, code in entities_luau.items():
        header = LUAU_HEADER_TEMPLATE.format(source_name=args.source)
        full_code = header + code
        out_path = os.path.join(args.out, f"{entity_name}.luau")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_code)
        print(f"✓ {entity_name} -> {out_path}")

    print(f"\nCompilacion exitosa: {len(entities_luau)} entidad(es) generada(s).")


if __name__ == "__main__":
    main()
