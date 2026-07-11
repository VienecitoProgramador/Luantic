#!/usr/bin/env python3
"""
desktop_app.py
Luantic -- editor de escritorio para EntityScript, hecho con Tkinter (viene
incluido con Python en Windows/Mac, no requiere instalar nada mas).

Luantic es software libre y de codigo abierto: cualquiera puede usarlo,
modificarlo y distribuirlo.

Arquitectura: esta app llama DIRECTO a las funciones de Compiler/ (via
CLI/es_build.compile_source), en el mismo proceso, sin servidor HTTP ni
navegador de por medio. Sigue habiendo una unica implementacion del
compilador -- esta es simplemente otra interfaz mas sobre el mismo
Compiler/, igual que CLI/es_build.py o Editor/webapp/server.py.

Uso:
    python3 Editor/desktop_app.py

Requisitos: Python 3.10+ con tkinter (incluido por defecto en la
instalacion estandar de Windows y macOS; en Linux puede requerir
`sudo apt install python3-tk` si no viene preinstalado).
"""

import os
import re
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zipfile
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from CLI.es_build import compile_source
from Compiler.Lexer.lexer_errors import LexError
from Compiler.Parser.syntax_errors import ParseError
from Compiler.Semantic.semantic_errors import SemanticError
from Compiler.Semantic.module_errors import ModuleError

COMPILER_ERROR_TYPES = (LexError, ParseError, SemanticError, ModuleError)


# =====================================================================
# Contenido de ejemplo
# =====================================================================

EXAMPLE_CODE = """entity Coin {
    value = 10

    position = (0, 3, 0)
    color = yellow
    anchored = true
    collision = false

    function Collect(player) {
        give player value
        destroy self
    }

    on touch(player) {
        Collect(player)
    }
}
"""

EXAMPLES = {
    "01 - Moneda (basico)": EXAMPLE_CODE,
    "02 - Herencia + dano": """entity Character {
    health = 100
    maxHealth = 100
}

# Los goblins son enemigos basicos: poca vida, sin loot especial.
entity Goblin extends Character {
    @respawnable(15)

    on spawn {
        health = maxHealth
    }

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            emit EnemyDefeated(self)
            destroy self
        } else {
            play "rbxassetid://9990001"
        }
    }
}
""",
    "03 - Leaderstats + score + funciones": """leaderstat Coins = 0
leaderstat Wins = 0

entity Coin {
    const RespawnDelay = 3
    value = 10
    score = Coins

    position = (0, 3, 0)
    color = "#FFD700"
    anchored = true
    collision = false

    function Collect(player) {
        give player value
        destroy self
    }

    on touch(player) {
        Collect(player)
    }
}

entity GameManager {
    @global

    on join(player) {
        message player "Bienvenido al juego!"
    }

    on timer(seconds) {
        for player in players {
            message player "Segui jugando!"
        }
    }
}
""",
    "04 - NPC con timers": """entity NPCVendor {
    const MaxGreets = 3
    greetCount = 0

    on interact(player) {
        greetCount += 1
        message player "Bienvenido al mercado, viajero."

        if greetCount > MaxGreets {
            give player 5
        }
    }

    function PlaySound() {
        play "rbxassetid://5551234"
    }

    on timer(seconds) {
        after 2 {
            PlaySound()
        }
    }
}
""",
}


# =====================================================================
# Paleta -- "carbon suave"
# =====================================================================
# Pensada para mirar mucho rato: nada de negro puro ni blanco puro.
# Un solo acento (menta apagado), diferenciacion por peso tipografico
# y espacio antes que por mas tonos de gris.

BG = "#1c1e1f"          # fondo base: carbon, no negro
BG_EDITOR = "#1c1e1f"
BG_PANEL = "#212325"    # panel de salida, un tono apenas mas claro
BG_RAISED = "#282a2c"   # botones secundarios / hover
BORDER = "#303234"

FG = "#d8d9d6"          # texto principal: hueso calido, no blanco puro
FG_DIM = "#8c8f8f"
FG_FAINT = "#4d4f50"

ACCENT = "#8fbfae"          # menta apagado -- unico acento de la app
ACCENT_HOVER = "#a3ccbc"
ACCENT_TEXT = "#16211d"      # texto sobre el acento (oscuro, buen contraste)

ERROR = "#d97b76"
ERROR_SOFT = "#e3a29e"
ERROR_BG = "#2c2120"

WARNING = "#cdab6c"
WARNING_SOFT = "#ddc496"

SYN_KEYWORD = "#b39ac4"
SYN_STRING = "#c2a077"
SYN_NUMBER = "#94b491"
SYN_COMMENT = "#5c5e5f"
SYN_BOOL = "#7fa7bd"
SYN_DECORATOR = "#cdab6c"

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

FONT_MONO = ("Consolas", 11) if IS_WIN else ("Menlo", 11) if IS_MAC else ("DejaVu Sans Mono", 11)
FONT_UI = ("Segoe UI", 10) if IS_WIN else ("Helvetica", 10)
FONT_UI_MED = (FONT_UI[0], 10, "bold")
FONT_BRAND = (FONT_UI[0], 13, "bold")

MOD_KEY = "Cmd" if IS_MAC else "Ctrl"

KEYWORDS = r"\b(entity|extends|function|on|const|leaderstat|if|else|for|in|return|emit|destroy|give|message|play|after|self|players)\b"
BOOLS = r"\b(true|false)\b"
DECORATORS = r"@\w+"
NUMBERS = r"\b\d+(\.\d+)?\b"
STRINGS = r'"[^"]*"'
COMMENTS = r"#.*"


# =====================================================================
# Gutter de numeros de linea
# =====================================================================

class LineNumberGutter(tk.Canvas):
    """Gutter de numeros de linea, discreto, con marca de linea con error."""

    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, bg=BG, highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        self.error_line = None

    def redraw(self, *_args):
        self.delete("all")
        if self.text_widget is None:
            return
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y_top, line_height = dline[1], dline[3]
            y_center = y_top + line_height / 2
            line_num = str(i).split(".")[0]
            is_error = self.error_line is not None and int(line_num) == self.error_line
            color = ERROR if is_error else FG_FAINT
            self.create_text(34, y_center, anchor="e", text=line_num, fill=color, font=FONT_MONO)
            i = self.text_widget.index(f"{i}+1line")

    def set_error_line(self, line):
        self.error_line = line
        self.redraw()

    def clear_markers(self):
        self.error_line = None
        self.redraw()


# =====================================================================
# Editor principal
# =====================================================================

class EntityScriptEditor:
    EDITOR_PAD_Y = 16  # padding vertical compartido entre gutter y code_text

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Luantic")
        self.root.geometry("1200x780")
        self.root.minsize(680, 480)
        self.root.configure(bg=BG)
        self.is_fullscreen = False

        self._apply_titlebar_theme()

        self.current_file_path = None
        self.last_compiled_files = None
        self.last_leaderstats_code = None
        self.autocompile_job = None
        self.highlight_job = None
        self.dirty = False
        self.output_visible = True

        self._configure_ttk()
        self._build_topbar()
        self._build_main_area()
        self._build_statusbar()
        self._bind_shortcuts()

        self.code_text.insert("1.0", EXAMPLE_CODE)
        self._on_code_change()
        self.compile()

    def _apply_titlebar_theme(self):
        """En Windows, pinta la barra de titulo nativa del mismo tono
        carbon que el resto de la app (Windows 11 / 10 build reciente).
        En otros sistemas la barra la controla el gestor de ventanas y
        no se puede recolorear desde Tkinter, asi que no hace nada."""
        if not IS_WIN:
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
            # DWMWA_CAPTION_COLOR (Windows 11) -- mismo tono que BG, en BGR
            bg_bgr = 0x00212422  # equivalente BGR de "#1c1e1f" aprox.
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(ctypes.c_int(bg_bgr)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass  # version de Windows sin soporte, o API no disponible

    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)

    # ----------------------------------------------------------------
    # estilos ttk
    # ----------------------------------------------------------------

    def _configure_ttk(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TPanedwindow", background=BG)
        style.configure(
            "Vertical.TScrollbar", background=BG, troughcolor=BG,
            bordercolor=BG, arrowcolor=FG_FAINT, relief="flat", width=9,
        )
        style.map("Vertical.TScrollbar", background=[("active", BORDER)])

    # ----------------------------------------------------------------
    # barra superior: marca, menus propios, acciones principales
    # ----------------------------------------------------------------

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG, height=60)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=BG)
        left.pack(side="left", fill="y", padx=(20, 4))

        brand_row = tk.Frame(left, bg=BG)
        brand_row.pack(side="top", anchor="w", pady=(9, 0))

        self.brand_dot = tk.Label(brand_row, text="●", bg=BG, fg=ACCENT, font=(FONT_UI[0], 9))
        self.brand_dot.pack(side="left")
        tk.Label(brand_row, text=" Luantic", bg=BG, fg=FG, font=FONT_BRAND).pack(side="left")
        self.filename_label = tk.Label(brand_row, text="  ·  editor.es", bg=BG, fg=FG_DIM, font=FONT_UI)
        self.filename_label.pack(side="left")

        menu_row = tk.Frame(left, bg=BG)
        menu_row.pack(side="top", anchor="w", pady=(2, 0))
        self._build_menu_button(menu_row, "Archivo", self._build_file_menu)
        self._build_menu_button(menu_row, "Ejemplos", self._build_examples_menu)
        self._build_menu_button(menu_row, "Ver", self._build_view_menu)
        self._build_menu_button(menu_row, "Ayuda", self._build_help_menu)

        right = tk.Frame(bar, bg=BG)
        right.pack(side="right", fill="y", padx=(0, 18))

        self.compile_btn = self._make_button(
            right, "▶  Compilar", self.compile, bg=ACCENT, fg=ACCENT_TEXT,
            hover=ACCENT_HOVER, primary=True,
        )
        self.compile_btn.pack(side="right", pady=14)

        self.output_toggle_btn = self._make_button(
            right, "▤  Salida", self._toggle_output, bg=BG_RAISED, fg=FG,
            hover="#313335", primary=False,
        )
        self.output_toggle_btn.pack(side="right", pady=14, padx=(0, 8))

        self.export_btn = self._make_button(
            right, "⇩  Exportar", self.export_zip, bg=BG_RAISED, fg=FG,
            hover="#313335", primary=False,
        )
        self.export_btn.pack(side="right", pady=14, padx=(0, 8))

        divider = tk.Frame(self.root, bg=BORDER, height=1)
        divider.pack(side="top", fill="x")

    def _make_button(self, parent, text, command, bg, fg, hover, primary):
        btn = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg, font=FONT_UI_MED,
            relief="flat", padx=16 if primary else 14, pady=8, cursor="hand2", bd=0,
            activebackground=hover, activeforeground=fg,
        )
        self._add_hover(btn, bg, hover)
        return btn

    def _build_menu_button(self, parent, label, populate_fn):
        btn = tk.Label(
            parent, text=label, bg=BG, fg=FG_DIM, font=FONT_UI,
            padx=8, pady=3, cursor="hand2",
        )
        btn.pack(side="left")

        menu = tk.Menu(
            self.root, tearoff=0, bg=BG_RAISED, fg=FG, bd=0,
            activebackground=ACCENT, activeforeground=ACCENT_TEXT,
            font=FONT_UI, relief="flat",
        )
        populate_fn(menu)

        def open_menu(event):
            menu.tk_popup(event.widget.winfo_rootx(), event.widget.winfo_rooty() + event.widget.winfo_height())

        btn.bind("<Button-1>", open_menu)
        btn.bind("<Enter>", lambda e: btn.config(fg=FG, bg=BG_RAISED))
        btn.bind("<Leave>", lambda e: btn.config(fg=FG_DIM, bg=BG))
        return btn

    def _build_file_menu(self, menu):
        menu.add_command(label="Nuevo", command=self.new_file, accelerator=f"{MOD_KEY}+N")
        menu.add_command(label="Abrir .es...", command=self.open_file, accelerator=f"{MOD_KEY}+O")
        menu.add_command(label="Guardar .es...", command=self.save_file, accelerator=f"{MOD_KEY}+S")
        menu.add_separator()
        menu.add_command(label="Exportar .zip con Luau...", command=self.export_zip, accelerator=f"{MOD_KEY}+E")
        menu.add_separator()
        menu.add_command(label="Salir", command=self.root.quit)

    def _build_examples_menu(self, menu):
        for label, code in EXAMPLES.items():
            menu.add_command(label=label, command=lambda c=code: self.load_example(c))

    def _build_view_menu(self, menu):
        self.wrap_var = tk.BooleanVar(value=False)
        menu.add_checkbutton(label="Ajuste de linea", variable=self.wrap_var, command=self._toggle_wrap)
        self.autocompile_var = tk.BooleanVar(value=True)
        menu.add_checkbutton(label="Autocompilar", variable=self.autocompile_var)
        menu.add_separator()
        menu.add_command(label="Mostrar/ocultar salida", command=self._toggle_output, accelerator=f"{MOD_KEY}+J")
        menu.add_separator()
        menu.add_command(label="Pantalla completa", command=self._toggle_fullscreen, accelerator="F11")

    def _build_help_menu(self, menu):
        menu.add_command(label="Atajos de teclado", command=self._show_shortcuts)
        menu.add_command(label="Acerca de Luantic", command=self._show_about)

    def _add_hover(self, widget, normal, hover):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal))

    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-e>", lambda e: self.export_zip())
        self.root.bind("<Control-Return>", lambda e: self.compile())
        self.root.bind("<Control-j>", lambda e: self._toggle_output())
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)
        if IS_MAC:
            self.root.bind("<Command-n>", lambda e: self.new_file())
            self.root.bind("<Command-o>", lambda e: self.open_file())
            self.root.bind("<Command-s>", lambda e: self.save_file())
            self.root.bind("<Command-e>", lambda e: self.export_zip())
            self.root.bind("<Command-Return>", lambda e: self.compile())
            self.root.bind("<Command-j>", lambda e: self._toggle_output())

    # ----------------------------------------------------------------
    # area principal: editor + salida
    # ----------------------------------------------------------------

    def _build_main_area(self):
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="top", fill="both", expand=True)

        self.paned = tk.PanedWindow(
            self.main, orient="horizontal", bg=BG, sashwidth=1, sashrelief="flat",
            bd=0, showhandle=False, sashpad=0,
        )
        self.paned.pack(fill="both", expand=True)

        self._build_editor_pane()
        self._build_output_pane()

    def _build_editor_pane(self):
        self.left = tk.Frame(self.paned, bg=BG)

        editor_frame = tk.Frame(self.left, bg=BG_EDITOR)
        editor_frame.pack(side="top", fill="both", expand=True)

        self.gutter = LineNumberGutter(editor_frame, None, width=42)
        self.gutter.pack(side="left", fill="y", pady=(self.EDITOR_PAD_Y, 0))

        self.code_text = tk.Text(
            editor_frame, bg=BG_EDITOR, fg=FG, insertbackground=ACCENT,
            font=FONT_MONO, relief="flat", padx=8, pady=self.EDITOR_PAD_Y, undo=True, wrap="none",
            selectbackground="#33463f", selectforeground=FG, bd=0,
            highlightthickness=0,
        )
        self.code_text.pack(side="left", fill="both", expand=True)
        self.gutter.text_widget = self.code_text

        self.code_text.bind("<KeyRelease>", self._on_code_change)
        self.code_text.bind("<MouseWheel>", lambda e: self.root.after(1, self.gutter.redraw))
        self.code_text.bind("<Button-4>", lambda e: self.root.after(1, self.gutter.redraw))
        self.code_text.bind("<Button-5>", lambda e: self.root.after(1, self.gutter.redraw))
        self.code_text.bind("<Configure>", lambda e: self.gutter.redraw())
        self.code_text.bind("<Tab>", self._insert_tab)
        self.code_text.bind("<<Modified>>", self._on_modified)

        code_scroll = ttk.Scrollbar(editor_frame, command=self._on_scroll, style="Vertical.TScrollbar")
        code_scroll.pack(side="right", fill="y")
        self.code_text.config(yscrollcommand=lambda *a: self._on_yscroll(code_scroll, *a))

        self.code_text.tag_configure("error_line", background=ERROR_BG)
        self._configure_syntax_tags()

        self.paned.add(self.left, minsize=280)

    def _build_output_pane(self):
        self.right = tk.Frame(self.paned, bg=BG)

        sep = tk.Frame(self.right, bg=BORDER, width=1)
        sep.pack(side="left", fill="y")

        right_inner = tk.Frame(self.right, bg=BG_PANEL)
        right_inner.pack(side="left", fill="both", expand=True)

        right_header = tk.Frame(right_inner, bg=BG_PANEL, height=34)
        right_header.pack(side="top", fill="x", padx=(16, 16), pady=(12, 0))
        right_header.pack_propagate(False)

        tk.Label(right_header, text="Salida", bg=BG_PANEL, fg=FG_DIM, font=FONT_UI).pack(side="left")
        self.output_summary_label = tk.Label(right_header, text="", bg=BG_PANEL, fg=FG_FAINT, font=FONT_UI)
        self.output_summary_label.pack(side="right")

        output_frame = tk.Frame(right_inner, bg=BG_PANEL)
        output_frame.pack(side="top", fill="both", expand=True, padx=(16, 0))

        self.output_text = tk.Text(
            output_frame, bg=BG_PANEL, fg=FG, font=FONT_MONO, relief="flat", padx=0, pady=12,
            state="disabled", wrap="word", bd=0, highlightthickness=0,
        )
        self.output_text.pack(side="left", fill="both", expand=True)

        out_scroll = ttk.Scrollbar(output_frame, command=self.output_text.yview, style="Vertical.TScrollbar")
        out_scroll.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=out_scroll.set)

        self.output_text.tag_configure("success", foreground=ACCENT, font=(FONT_MONO[0], 11, "bold"))
        self.output_text.tag_configure("error_title", foreground=ERROR, font=(FONT_MONO[0], 11, "bold"))
        self.output_text.tag_configure("error_body", foreground=ERROR_SOFT)
        self.output_text.tag_configure("warning", foreground=WARNING_SOFT)
        self.output_text.tag_configure("file_header", foreground=FG_DIM, font=(FONT_MONO[0], 10, "bold"))
        self.output_text.tag_configure("code", foreground="#c7c8c5", font=FONT_MONO)
        self.output_text.tag_configure("dim", foreground=FG_FAINT)

        self.paned.add(self.right, minsize=280)

    def _configure_syntax_tags(self):
        self.code_text.tag_configure("kw", foreground=SYN_KEYWORD)
        self.code_text.tag_configure("bool", foreground=SYN_BOOL)
        self.code_text.tag_configure("string", foreground=SYN_STRING)
        self.code_text.tag_configure("number", foreground=SYN_NUMBER)
        self.code_text.tag_configure("comment", foreground=SYN_COMMENT, font=(FONT_MONO[0], FONT_MONO[1], "italic"))
        self.code_text.tag_configure("decorator", foreground=SYN_DECORATOR)

    # ----------------------------------------------------------------
    # barra de estado
    # ----------------------------------------------------------------

    def _build_statusbar(self):
        divider = tk.Frame(self.root, bg=BORDER, height=1)
        divider.pack(side="bottom", fill="x")

        bar = tk.Frame(self.root, bg=BG, height=28)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        self.compile_indicator = tk.Label(
            bar, text="●  Listo", bg=BG, fg=FG_DIM, font=FONT_UI, anchor="w", padx=16,
        )
        self.compile_indicator.pack(side="left", fill="y")

        self.timing_label = tk.Label(bar, text="", bg=BG, fg=FG_FAINT, font=FONT_UI, anchor="e", padx=16)
        self.timing_label.pack(side="right", fill="y")

        self.char_count_label = tk.Label(bar, text="", bg=BG, fg=FG_FAINT, font=FONT_UI, anchor="e", padx=6)
        self.char_count_label.pack(side="right", fill="y")

    # ----------------------------------------------------------------
    # toggle de panel de salida
    # ----------------------------------------------------------------

    def _toggle_output(self):
        self.output_visible = not self.output_visible
        if self.output_visible:
            self.paned.add(self.right, minsize=280)
        else:
            self.paned.forget(self.right)

    # ----------------------------------------------------------------
    # helpers de UI
    # ----------------------------------------------------------------

    def _toggle_wrap(self):
        self.code_text.config(wrap="word" if self.wrap_var.get() else "none")

    def _on_scroll(self, *args):
        self.code_text.yview(*args)
        self.gutter.redraw()

    def _on_yscroll(self, scrollbar, *args):
        scrollbar.set(*args)
        self.gutter.redraw()

    def _insert_tab(self, event):
        self.code_text.insert(tk.INSERT, "    ")
        return "break"

    def _on_modified(self, event=None):
        if self.code_text.edit_modified():
            self.code_text.edit_modified(False)

    def _on_code_change(self, event=None):
        char_count = len(self.code_text.get("1.0", "end-1c"))
        self.char_count_label.config(text=f"{char_count} caracteres")
        self.gutter.redraw()
        self._schedule_highlight()
        self._maybe_autocompile()
        if not self.dirty:
            self.dirty = True
            self._update_title()

    def _schedule_highlight(self):
        if self.highlight_job is not None:
            self.root.after_cancel(self.highlight_job)
        self.highlight_job = self.root.after(120, self._apply_syntax_highlight)

    def _apply_syntax_highlight(self):
        text = self.code_text.get("1.0", "end-1c")
        for tag in ("kw", "bool", "string", "number", "comment", "decorator"):
            self.code_text.tag_remove(tag, "1.0", "end")

        def tag_pattern(pattern, tag):
            for m in re.finditer(pattern, text):
                start = f"1.0+{m.start()}c"
                end = f"1.0+{m.end()}c"
                self.code_text.tag_add(tag, start, end)

        tag_pattern(KEYWORDS, "kw")
        tag_pattern(BOOLS, "bool")
        tag_pattern(NUMBERS, "number")
        tag_pattern(DECORATORS, "decorator")
        tag_pattern(STRINGS, "string")
        tag_pattern(COMMENTS, "comment")

    def _maybe_autocompile(self):
        if not self.autocompile_var.get():
            return
        if self.autocompile_job is not None:
            self.root.after_cancel(self.autocompile_job)
        self.autocompile_job = self.root.after(500, self.compile)

    def _set_status(self, text, kind="ok"):
        indicator_colors = {"ok": ACCENT, "error": ERROR, "warning": WARNING}
        indicator_text = {"ok": "●  Listo", "error": "●  Error", "warning": "●  Con advertencias"}
        color = indicator_colors.get(kind, ACCENT)
        self.compile_indicator.config(fg=color, text=indicator_text.get(kind, "●  Listo"))
        self.brand_dot.config(fg=color)

    def _update_title(self):
        name = os.path.basename(self.current_file_path) if self.current_file_path else "editor.es"
        marker = " ●" if self.dirty else ""
        self.filename_label.config(text=f"  ·  {name}{marker}")
        self.root.title(f"Luantic · {name}{marker}" if self.current_file_path else f"Luantic{marker}")

    # ----------------------------------------------------------------
    # compilacion (llama directo al Compiler/)
    # ----------------------------------------------------------------

    def compile(self):
        source = self.code_text.get("1.0", "end-1c")

        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.code_text.tag_remove("error_line", "1.0", "end")
        self.gutter.clear_markers()

        if not source.strip():
            self.output_text.insert("end", 'Escribi codigo EntityScript y presiona "Compilar".', "dim")
            self.output_text.config(state="disabled")
            self._set_status("Listo.", "ok")
            self.output_summary_label.config(text="")
            self.last_compiled_files = None
            return

        t0 = time.perf_counter()

        # --- ESTA ES LA UNICA LLAMADA AL COMPILADOR ---
        # Misma funcion que usa CLI/es_build.py y Editor/webapp/server.py.
        try:
            entities_luau, warnings, leaderstats_luau = compile_source(
                source, "editor.es", preserve_comments=False
            )
        except COMPILER_ERROR_TYPES as e:
            self._render_error(e, source)
            self.last_compiled_files = None
            self._show_timing(t0)
            return
        except Exception as e:
            self._render_error_raw("InternalError", str(e), None, source)
            self.last_compiled_files = None
            self._show_timing(t0)
            return

        self.last_compiled_files = dict(entities_luau)
        self.last_leaderstats_code = leaderstats_luau
        self._render_success(entities_luau, leaderstats_luau, warnings)
        self._show_timing(t0)
        self.dirty = False
        self._update_title()

    def _show_timing(self, t0):
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.timing_label.config(text=f"{elapsed_ms:.0f} ms")

    def _render_success(self, entities, leaderstats_code, warnings):
        self.output_text.insert("end", "✓  Compilacion exitosa\n\n", "success")

        for w in warnings:
            self.output_text.insert("end", f"⚠  {w}\n", "warning")
        if warnings:
            self.output_text.insert("end", "\n")

        if leaderstats_code:
            self.output_text.insert("end", "LeaderstatsSetup.luau\n", "file_header")
            self.output_text.insert("end", leaderstats_code + "\n\n", "code")

        for name, code in entities.items():
            self.output_text.insert("end", f"{name}.luau\n", "file_header")
            self.output_text.insert("end", code + "\n\n", "code")

        self.output_text.config(state="disabled")
        kind = "warning" if warnings else "ok"
        summary = f"{len(entities)} archivo(s)" + (f" · {len(warnings)} advertencia(s)" if warnings else "")
        self.output_summary_label.config(text=summary)
        self._set_status("Compilado.", kind)

    def _render_error(self, error, source):
        code = getattr(error, "code", type(error).__name__)
        message = getattr(error, "message", str(error))
        line = getattr(error, "line", None)
        self._render_error_raw(code, message, line, source)

    def _render_error_raw(self, code, message, line, source):
        self.output_text.insert("end", "✕  Error de compilacion\n", "error_title")
        self.output_text.insert("end", f"[{code}]\n\n", "dim")
        self.output_text.insert("end", f"{message}\n", "error_body")
        if line:
            lines = source.split("\n")
            if 1 <= line <= len(lines):
                self.output_text.insert("end", f"\nLinea {line}\n", "dim")
                self.output_text.insert("end", f"{lines[line - 1].strip()}\n", "code")
                self.code_text.tag_add("error_line", f"{line}.0", f"{line}.end")
                self.gutter.set_error_line(line)
                self.code_text.see(f"{line}.0")
        self.output_text.config(state="disabled")
        self.output_summary_label.config(text="")
        status = f"Error: {code}" + (f" — linea {line}" if line else "")
        self._set_status(status, "error")

    # ----------------------------------------------------------------
    # archivo
    # ----------------------------------------------------------------

    def new_file(self):
        if not self._confirm_discard_changes():
            return
        self.code_text.delete("1.0", "end")
        self.current_file_path = None
        self.dirty = False
        self._update_title()
        self._on_code_change()
        self.compile()

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo EntityScript", filetypes=[("EntityScript", "*.es"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            messagebox.showerror("Error al abrir", str(e))
            return
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", content)
        self.current_file_path = path
        self.dirty = False
        self._update_title()
        self._on_code_change()
        self.compile()

    def save_file(self):
        path = self.current_file_path
        if not path:
            path = filedialog.asksaveasfilename(
                title="Guardar como", defaultextension=".es",
                filetypes=[("EntityScript", "*.es"), ("Todos los archivos", "*.*")],
            )
            if not path:
                return
        content = self.code_text.get("1.0", "end-1c")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            messagebox.showerror("Error al guardar", str(e))
            return
        self.current_file_path = path
        self.dirty = False
        self._update_title()
        self._set_status("Guardado", "ok")

    def export_zip(self):
        if not self.last_compiled_files:
            self.compile()
        if not self.last_compiled_files:
            messagebox.showwarning("Nada para exportar", "Corregi los errores de compilacion antes de exportar.")
            return

        path = filedialog.asksaveasfilename(
            title="Exportar Luau como .zip", defaultextension=".zip",
            filetypes=[("Archivo ZIP", "*.zip")], initialfile="entityscript_output.zip",
        )
        if not path:
            return

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if self.last_leaderstats_code:
                zf.writestr("LeaderstatsSetup.luau", self.last_leaderstats_code)
            for name, code in self.last_compiled_files.items():
                zf.writestr(f"{name}.luau", code)

        try:
            with open(path, "wb") as f:
                f.write(buffer.getvalue())
        except OSError as e:
            messagebox.showerror("Error al exportar", str(e))
            return

        self._set_status("Exportado", "ok")
        messagebox.showinfo("Exportado", f"Se exportaron {len(self.last_compiled_files)} archivo(s) Luau a:\n{path}")

    def _confirm_discard_changes(self):
        if not self.dirty:
            return True
        return messagebox.askokcancel("Nuevo archivo", "Descartar el codigo actual y empezar uno nuevo?")

    def load_example(self, code):
        if not self._confirm_discard_changes():
            return
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", code)
        self.current_file_path = None
        self.dirty = False
        self._update_title()
        self._on_code_change()
        self.compile()

    # ----------------------------------------------------------------
    # ayuda
    # ----------------------------------------------------------------

    def _show_shortcuts(self):
        messagebox.showinfo(
            "Atajos de teclado",
            f"{MOD_KEY}+N   Nuevo archivo\n"
            f"{MOD_KEY}+O   Abrir .es\n"
            f"{MOD_KEY}+S   Guardar .es\n"
            f"{MOD_KEY}+E   Exportar .zip\n"
            f"{MOD_KEY}+Enter   Compilar\n"
            f"{MOD_KEY}+J   Mostrar/ocultar salida\n"
            f"F11   Pantalla completa\n"
            f"Esc   Salir de pantalla completa",
        )

    def _show_about(self):
        messagebox.showinfo(
            "Acerca de Luantic",
            "Luantic v0.2\n\n"
            "Aviso: este proyecto es muy inestable. Es un mini proyecto\n"
            "hecho por diversion y como testeo de desarrollo de codigo,\n"
            "no un producto terminado ni estable.\n\n"
            "Luantic es un editor que transpila un lenguaje simplificado\n"
            "de entidades y eventos hacia Luau.\n\n"
            "Es 100% open source: el codigo fuente esta disponible en\n"
            "GitHub y cualquiera puede usarlo, modificarlo y publicar\n"
            "sus propias versiones de Luantic libremente -- incluyendo\n"
            "cambiar o rehacer por completo la interfaz.\n\n"
            "Repositorio: https://github.com/VienecitoProgramador/Luantic\n\n"
            "Creador: Vienestor\n"
            "TikTok: tiktok.com/@vienestorstudio",
        )



def main():
    root = tk.Tk()
    EntityScriptEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()