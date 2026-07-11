#!/usr/bin/env python3
"""
server.py
Servidor HTTP local minimo (solo libreria estandar, sin dependencias nuevas)
que expone el UNICO compilador de EntityScript (Compiler/) a una interfaz
web servida desde el mismo proceso.

Arquitectura (decision tomada tras revision de diseño):

    Editor (HTML/JS, solo interfaz)
        │  fetch("/compile", { source: "..." })
        ▼
    server.py (este archivo)
        │  llama directamente a funciones de CLI/es_build.py
        ▼
    Compiler/  (Lexer -> Parser -> Semantic -> Transpiler, Python puro)
        │
        ▼
    Luau generado (respuesta JSON)

Esto garantiza que EXISTE UNA SOLA IMPLEMENTACION del compilador. El editor
JS no tiene absolutamente ninguna logica de tokenizado/parseo/emision -- solo
manda texto y muestra la respuesta. Cualquier feature nueva del lenguaje se
implementa una unica vez en Compiler/ y automaticamente esta disponible aqui,
en el CLI, y en cualquier futuro cliente (VSCode, etc.) que hable el mismo
protocolo HTTP.

Endpoints:
    GET  /                  -> sirve la interfaz (index.html)
    POST /compile           -> compila el codigo y devuelve el Luau generado
    POST /save              -> guarda el codigo actual en disco (autosave)
    GET  /load               -> devuelve el ultimo codigo guardado
    POST /download-zip      -> arma un .zip con todos los .luau generados

Uso:
    python3 Editor/webapp/server.py [--port 8765]
    Luego abrir http://localhost:8765 en el navegador.
"""

import argparse
import io
import json
import os
import socket
import sys
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from CLI.es_build import compile_source
from Compiler.Lexer.lexer_errors import LexError
from Compiler.Parser.syntax_errors import ParseError
from Compiler.Semantic.semantic_errors import SemanticError
from Compiler.Semantic.module_errors import ModuleError

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
AUTOSAVE_PATH = os.path.join(os.path.dirname(__file__), ".autosave.es")

COMPILER_ERROR_TYPES = (LexError, ParseError, SemanticError, ModuleError)

MAX_BODY_SIZE = 2 * 1024 * 1024  # 2MB, generoso para codigo fuente de texto


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silencia el log por defecto, ruidoso para un uso local simple

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, content_type: str):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict | None:
        """
        Lee y parsea el body JSON de forma robusta. Retorna None (y ya
        responde el error al cliente) si algo falla, para que el caller
        simplemente haga `if data is None: return`.
        """
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            self._send_json(400, {"ok": False, "error": {"code": "BadRequest", "message": "Content-Length invalido", "line": None}})
            return None

        if length <= 0:
            self._send_json(400, {"ok": False, "error": {"code": "BadRequest", "message": "Cuerpo de peticion vacio", "line": None}})
            return None

        if length > MAX_BODY_SIZE:
            self._send_json(413, {"ok": False, "error": {"code": "PayloadTooLarge", "message": "El codigo enviado es demasiado grande", "line": None}})
            return None

        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"ok": False, "error": {"code": "BadRequest", "message": "JSON invalido", "line": None}})
            return None

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
        elif self.path == "/app.js":
            self._send_file(os.path.join(STATIC_DIR, "app.js"), "application/javascript; charset=utf-8")
        elif self.path == "/style.css":
            self._send_file(os.path.join(STATIC_DIR, "style.css"), "text/css; charset=utf-8")
        elif self.path == "/load":
            self._handle_load()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_load(self):
        """Devuelve el ultimo codigo autoguardado, o vacio si nunca se guardo nada."""
        source = ""
        if os.path.isfile(AUTOSAVE_PATH):
            try:
                with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
                    source = f.read()
            except OSError:
                pass
        self._send_json(200, {"ok": True, "source": source})

    def do_POST(self):
        if self.path == "/compile":
            self._handle_compile()
        elif self.path == "/save":
            self._handle_save()
        elif self.path == "/download-zip":
            self._handle_download_zip()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_save(self):
        data = self._read_json_body()
        if data is None:
            return
        source = data.get("source", "")
        try:
            with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
                f.write(source)
        except OSError as e:
            self._send_json(500, {"ok": False, "error": {"code": "SaveFailed", "message": str(e), "line": None}})
            return
        self._send_json(200, {"ok": True})

    def _handle_compile(self):
        data = self._read_json_body()
        if data is None:
            return

        source = data.get("source", "")
        preserve_comments = bool(data.get("preserve_comments", False))

        # --- ESTA ES LA UNICA LLAMADA AL COMPILADOR ---
        # Reutiliza exactamente la misma funcion que usa CLI/es_build.py,
        # que a su vez recorre Compiler/Lexer -> Parser -> Semantic -> Transpiler.
        try:
            entities_luau, warnings, leaderstats_luau = compile_source(
                source, "editor.es", preserve_comments=preserve_comments
            )
        except COMPILER_ERROR_TYPES as e:
            self._send_json(200, {
                "ok": False,
                "error": {
                    "code": getattr(e, "code", type(e).__name__),
                    "message": getattr(e, "message", str(e)),
                    "line": getattr(e, "line", None),
                },
            })
            return
        except Exception as e:
            # Cualquier error inesperado (bug real del compilador) se reporta
            # igual, sin caer en un 500 opaco, para que la interfaz lo muestre.
            self._send_json(200, {
                "ok": False,
                "error": {"code": "InternalError", "message": str(e), "line": None},
            })
            return

        self._send_json(200, {
            "ok": True,
            "entities": entities_luau,
            "leaderstats": leaderstats_luau,
            "warnings": [str(w) for w in warnings],
        })

    def _handle_download_zip(self):
        """
        Compila el codigo actual y arma un unico .zip con todos los .luau
        generados, para que el usuario descargue un solo archivo en vez de
        que el navegador dispare N descargas sueltas (una por entidad).
        """
        data = self._read_json_body()
        if data is None:
            return

        source = data.get("source", "")
        preserve_comments = bool(data.get("preserve_comments", False))

        try:
            entities_luau, _warnings, leaderstats_luau = compile_source(
                source, "editor.es", preserve_comments=preserve_comments
            )
        except COMPILER_ERROR_TYPES as e:
            self._send_json(200, {
                "ok": False,
                "error": {
                    "code": getattr(e, "code", type(e).__name__),
                    "message": getattr(e, "message", str(e)),
                    "line": getattr(e, "line", None),
                },
            })
            return
        except Exception as e:
            self._send_json(200, {"ok": False, "error": {"code": "InternalError", "message": str(e), "line": None}})
            return

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if leaderstats_luau:
                zf.writestr("LeaderstatsSetup.luau", leaderstats_luau)
            for name, code in entities_luau.items():
                zf.writestr(f"{name}.luau", code)

        body = buffer.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", 'attachment; filename="entityscript_output.zip"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def main():
    parser = argparse.ArgumentParser(description="Servidor local del Editor de EntityScript")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="No abrir el navegador automaticamente")
    args = parser.parse_args()

    if not _port_is_free(args.port):
        print(f"✗ El puerto {args.port} ya esta en uso.")
        print(f"  Es probable que ya tengas otra instancia del editor corriendo.")
        print(f"  Opciones:")
        print(f"    - Si ya lo tenes abierto, andá directo a http://127.0.0.1:{args.port}")
        print(f"    - Si no, cerrá el proceso anterior o probá con otro puerto:")
        print(f"        python3 Editor/webapp/server.py --port {args.port + 1}")
        sys.exit(1)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"EntityScript Editor corriendo en {url}")
    print("Presiona Ctrl+C para detener.")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")


if __name__ == "__main__":
    main()
