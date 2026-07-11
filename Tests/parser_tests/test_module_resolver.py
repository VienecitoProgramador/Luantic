"""
test_module_resolver.py
Pruebas de resolucion real de `use` (imports entre archivos .es):
- import valido que fusiona entidades y permite `extends` cross-file.
- modulo inexistente.
- import circular (deteccion sin recursion infinita).

Usa archivos temporales reales en disco, ya que la resolucion de modulos
es explicitamente una operacion de filesystem (ver module_resolver.py).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import shutil
import tempfile
import pytest

from Compiler.Lexer.tokenizer import tokenize_source
from Compiler.Parser.grammar_rules import parse_tokens
from Compiler.Semantic.module_resolver import resolve_program
from Compiler.Semantic.module_errors import (
    ModuleNotFoundError_,
    CircularImportError,
    DuplicateEntityAcrossModulesError,
)
from Compiler.Semantic.type_checker import check_program


@pytest.fixture
def tmp_project():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _parse_file(path):
    with open(path, encoding="utf-8") as f:
        source = f.read()
    tokens, comments = tokenize_source(source, path)
    return parse_tokens(tokens, comments)


def test_use_resolves_nested_module_and_merges_entities(tmp_project):
    _write(
        os.path.join(tmp_project, "Combat", "DamageTypes.es"),
        "entity Character {\n    health: Number = 100\n}\n",
    )
    main_path = os.path.join(tmp_project, "main.es")
    _write(
        main_path,
        "use Combat.DamageTypes\n\nentity Goblin extends Character {\n    on damage(amount) {\n        health -= amount\n    }\n}\n",
    )

    program = _parse_file(main_path)
    resolved = resolve_program(program, main_path)

    names = [e.name for e in resolved.entities]
    assert "Character" in names
    assert "Goblin" in names
    assert resolved.imports == []

    # el type-checker debe aceptar `health` como heredada de Character
    symbols = check_program(resolved)
    assert symbols.resolve_property_type("Goblin", "health") == "Number"


def test_use_missing_module_raises(tmp_project):
    main_path = os.path.join(tmp_project, "main.es")
    _write(main_path, "use NoExiste.Modulo\n\nentity Foo {\n    x: Number = 1\n}\n")

    program = _parse_file(main_path)
    with pytest.raises(ModuleNotFoundError_):
        resolve_program(program, main_path)


def test_circular_import_raises_without_infinite_recursion(tmp_project):
    a_path = os.path.join(tmp_project, "a.es")
    b_path = os.path.join(tmp_project, "b.es")
    _write(a_path, "use b\nentity A {\n    x: Number = 1\n}\n")
    _write(b_path, "use a\nentity B {\n    y: Number = 2\n}\n")

    program = _parse_file(a_path)
    with pytest.raises(CircularImportError):
        resolve_program(program, a_path)


def test_use_deduplicates_entities_imported_twice(tmp_project):
    """Si dos modulos distintos importan la misma entidad base, no debe
    duplicarse en el Program final (lo cual rompería DuplicateEntityError)."""
    _write(
        os.path.join(tmp_project, "Shared.es"),
        "entity Base {\n    value: Number = 1\n}\n",
    )
    _write(
        os.path.join(tmp_project, "ModA.es"),
        "use Shared\nentity A extends Base {\n    on spawn {\n        value = 2\n    }\n}\n",
    )
    main_path = os.path.join(tmp_project, "main.es")
    _write(
        main_path,
        "use Shared\nuse ModA\n\nentity B extends Base {\n    on spawn {\n        value = 3\n    }\n}\n",
    )

    program = _parse_file(main_path)
    resolved = resolve_program(program, main_path)
    names = [e.name for e in resolved.entities]
    assert names.count("Base") == 1
    check_program(resolved)  # no debe lanzar DuplicateEntityError


def test_different_files_with_same_entity_name_raises(tmp_project):
    """
    Bug real corregido: antes, si a.es y b.es declaraban ambos `entity Coin`
    de forma INDEPENDIENTE (no el mismo archivo importado dos veces), el
    resolver silenciaba la colision y usaba arbitrariamente la primera que
    encontraba, descartando la segunda sin ningun aviso. Ahora esto debe
    ser un error explicito.
    """
    _write(os.path.join(tmp_project, "a.es"), "entity Coin {\n    value = 5\n}\n")
    _write(os.path.join(tmp_project, "b.es"), "entity Coin {\n    value = 999\n}\n")
    main_path = os.path.join(tmp_project, "main.es")
    _write(main_path, "use a\nuse b\n\nentity Foo {\n    x = 1\n}\n")

    program = _parse_file(main_path)
    with pytest.raises(DuplicateEntityAcrossModulesError):
        resolve_program(program, main_path)
