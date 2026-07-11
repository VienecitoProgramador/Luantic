#!/bin/bash
# Doble clic (o ./abrir_editor.sh desde terminal) para abrir el Editor de
# EntityScript en Mac/Linux.
# Requiere Python 3.10+ instalado (con tkinter; en Linux puede requerir
# `sudo apt install python3-tk` si no viene preinstalado).

cd "$(dirname "$0")"
python3 Editor/desktop_app.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Hubo un problema al abrir el editor."
    echo "Si el error menciona 'tkinter', instalalo con:"
    echo "  sudo apt install python3-tk    (Ubuntu/Debian)"
    read -p "Presiona Enter para cerrar..."
fi
