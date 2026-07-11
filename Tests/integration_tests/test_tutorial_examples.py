"""
test_tutorial_examples.py
Compila los 50 ejemplos progresivos de Examples/tutorial/ y confirma que
TODOS generan Luau sin errores. Estos archivos son la puerta de entrada
de un usuario nuevo al lenguaje -- si alguno se rompe, alguien
aprendiendo va a pensar que es su culpa, no un bug del ejemplo.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import glob
from CLI.es_build import compile_source


def _tutorial_dir():
    return os.path.join(os.path.dirname(__file__), "..", "..", "Examples", "tutorial")


def _find_tutorial_examples():
    # Solo los archivos numerados 01-50 en la raiz de tutorial/, no los
    # de la subcarpeta Shared/ (esos se importan via `use`, no se
    # compilan solos -- ver 48_import_use.es).
    pattern = os.path.join(_tutorial_dir(), "*.es")
    return sorted(glob.glob(pattern))


def test_exactly_50_tutorial_examples_exist():
    examples = _find_tutorial_examples()
    assert len(examples) == 50, f"se esperaban 50 ejemplos, se encontraron {len(examples)}"


def test_all_50_tutorial_examples_compile_without_errors():
    examples = _find_tutorial_examples()
    failures = []

    for path in examples:
        name = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        try:
            entities_luau, warnings, leaderstats_luau = compile_source(source, path)
        except Exception as e:
            failures.append(f"{name}: {type(e).__name__}: {e}")
            continue

        # Todo ejemplo debe generar al menos una entidad o un leaderstat;
        # un ejemplo que compila pero no genera nada util seria un ejemplo mal armado.
        if not entities_luau and not leaderstats_luau:
            failures.append(f"{name}: compilo pero no genero ninguna entidad ni leaderstat")

    assert not failures, "Ejemplos del tutorial con errores:\n" + "\n".join(failures)


def test_tutorial_examples_have_explanatory_comments():
    """
    Cada ejemplo del tutorial debe tener al menos un comentario, ya que
    su proposito es explicar un concepto, no solo mostrar sintaxis
    desnuda. Esto no valida CALIDAD del comentario, solo que exista.
    """
    examples = _find_tutorial_examples()
    missing_comments = []

    for path in examples:
        name = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        if "#" not in source:
            missing_comments.append(name)

    assert not missing_comments, "Ejemplos sin ningun comentario explicativo:\n" + "\n".join(missing_comments)
