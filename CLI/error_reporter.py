"""
error_reporter.py
Formatea errores del Lexer/Parser/Semantic de forma consistente para el CLI,
mostrando codigo, linea y mensaje accionable (nunca solo un traceback crudo).
"""

import sys


def report_error(source_lines: list[str], error) -> None:
    line_no = getattr(error, "line", None)
    code = getattr(error, "code", type(error).__name__)
    message = getattr(error, "message", str(error))

    print(f"\n✗ Error de compilacion [{code}]", file=sys.stderr)
    if line_no and 1 <= line_no <= len(source_lines):
        print(f"  Linea {line_no}: {source_lines[line_no - 1].strip()}", file=sys.stderr)
    print(f"  {message}\n", file=sys.stderr)


def report_warnings(warnings: list) -> None:
    if not warnings:
        return
    print(f"\n⚠ {len(warnings)} advertencia(s):", file=sys.stderr)
    for w in warnings:
        print(f"  {w}", file=sys.stderr)
    print("", file=sys.stderr)
