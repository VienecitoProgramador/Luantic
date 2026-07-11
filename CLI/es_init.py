#!/usr/bin/env python3
"""
es_init.py
Genera la estructura minima de un proyecto EntityScript nuevo:

    mi_juego/
        src/
            main.es
        build/          (vacio, destino de es_build)
        es.config.json  (configuracion del proyecto)

Uso:
    python es_init.py <nombre_proyecto>
"""

import argparse
import os
import json

DEFAULT_MAIN_ES = """entity Coin {
    points: Number = 10

    on touch(player) {
        give player points
        destroy self
    }
}
"""

DEFAULT_CONFIG = {
    "name": "mi_juego",
    "version": "0.1.0",
    "source_dir": "src",
    "output_dir": "build",
    "preserve_comments": False,
}


def main():
    parser = argparse.ArgumentParser(description="Crea un proyecto EntityScript nuevo")
    parser.add_argument("project_name")
    args = parser.parse_args()

    root = args.project_name
    os.makedirs(os.path.join(root, "src"), exist_ok=True)
    os.makedirs(os.path.join(root, "build"), exist_ok=True)

    with open(os.path.join(root, "src", "main.es"), "w", encoding="utf-8") as f:
        f.write(DEFAULT_MAIN_ES)

    config = dict(DEFAULT_CONFIG)
    config["name"] = args.project_name
    with open(os.path.join(root, "es.config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"✓ Proyecto '{args.project_name}' creado en ./{root}")
    print(f"  Siguiente paso: python CLI/es_build.py {root}/src/main.es --out {root}/build")


if __name__ == "__main__":
    main()
