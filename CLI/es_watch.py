#!/usr/bin/env python3
"""
es_watch.py
Recompila un archivo .es automaticamente cada vez que detecta un cambio
en disco (polling simple, sin dependencias externas de filesystem-events
para mantener el CLI liviano en v0.1).

Uso:
    python es_watch.py <archivo.es> [--out DIR]
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from CLI.es_build import compile_source
from CLI.error_reporter import report_error, report_warnings
from Compiler.Lexer.lexer_errors import LexError
from Compiler.Parser.syntax_errors import ParseError
from Compiler.Semantic.semantic_errors import SemanticError
from Compiler.Semantic.module_errors import ModuleError

POLL_INTERVAL_SECONDS = 0.5


def _build_once(source_path: str, out_dir: str):
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        # Ventana de guardado atomico: el archivo desaparecio un instante.
        # Se ignora este ciclo, el proximo poll lo va a encontrar de nuevo.
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ no se pudo leer {source_path} ({e}), reintentando...")
        return

    source_lines = source.splitlines()

    try:
        entities_luau, warnings, leaderstats_luau = compile_source(source, source_path)
    except (LexError, ParseError, SemanticError, ModuleError) as e:
        report_error(source_lines, e)
        return

    report_warnings(warnings)
    os.makedirs(out_dir, exist_ok=True)

    if leaderstats_luau:
        with open(os.path.join(out_dir, "LeaderstatsSetup.luau"), "w", encoding="utf-8") as f:
            f.write(leaderstats_luau)

    for entity_name, code in entities_luau.items():
        out_path = os.path.join(out_dir, f"{entity_name}.luau")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
    print(f"[{time.strftime('%H:%M:%S')}] ✓ recompilado: {len(entities_luau)} entidad(es)")


def main():
    parser = argparse.ArgumentParser(description="Recompila .es en cada cambio")
    parser.add_argument("source")
    parser.add_argument("--out", default="./build")
    args = parser.parse_args()

    print(f"Observando {args.source} (Ctrl+C para salir)...")
    last_mtime = None
    _build_once(args.source, args.out)
    last_mtime = _safe_getmtime(args.source)

    try:
        while True:
            time.sleep(POLL_INTERVAL_SECONDS)
            mtime = _safe_getmtime(args.source)
            if mtime is not None and mtime != last_mtime:
                last_mtime = mtime
                _build_once(args.source, args.out)
    except KeyboardInterrupt:
        print("\nDetenido.")


def _safe_getmtime(path: str) -> float | None:
    """
    Envuelve os.path.getmtime protegiendo contra la ventana en la que un
    archivo puede no existir momentaneamente (algunos editores de texto
    hacen 'guardado atomico': borran y recrean el archivo al guardar).
    Sin esto, es_watch podia morir con FileNotFoundError justo cuando el
    usuario estaba trabajando activamente.
    """
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


if __name__ == "__main__":
    main()
