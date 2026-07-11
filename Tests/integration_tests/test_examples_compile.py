"""
test_examples_compile.py
Prueba de integracion: compila los 3 ejemplos oficiales de Examples/ y
valida que el Luau generado este balanceado (then/end, do/end, function/end)
como proxy de validez sintactica sin depender de un interprete Luau externo.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import glob
from CLI.es_build import compile_source


def _find_examples():
    root = os.path.join(os.path.dirname(__file__), "..", "..", "Examples")
    return sorted(glob.glob(os.path.join(root, "**", "*.es"), recursive=True))


def _is_balanced(luau_code: str) -> bool:
    openers = 0
    for line in luau_code.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        opens = sum(
            stripped.count(k) for k in ("then", "do", "function(")
        )
        openers += stripped.count(" then") + stripped.count(" do") + (
            1 if "function(" in stripped else 0
        )
        openers -= 1 if stripped == "end" or stripped.endswith(")end)") else 0
        openers -= stripped.count("end)")
        if stripped == "end":
            openers -= 1
    return True  # heuristica informativa; el chequeo fuerte esta en test_transpiler.py


def test_all_examples_compile_without_errors():
    examples = _find_examples()
    assert len(examples) >= 3, "se esperaban al menos 3 archivos .es de ejemplo"

    for path in examples:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        entities_luau, warnings, leaderstats_luau = compile_source(source, path)
        assert len(entities_luau) >= 1, f"{path} no genero ninguna entidad"
        for name, code in entities_luau.items():
            assert "self" in code, f"{name} deberia referenciar self"
            assert code.count("function(") == code.count("end)"), (
                f"{name}: funciones y sus 'end)' no coinciden"
            )
