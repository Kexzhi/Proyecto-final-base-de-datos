# ui_widgets.py
# -----------------------------------------
# Widgets reutilizables:
# - carga de logo
# - barra de navegación (NavBar)
# - helpers para entradas con etiqueta y fechas
# - helper para mostrar mensaje si falta tabla
# -----------------------------------------

import os
import customtkinter as ctk
from PIL import Image

from settings import (
    COLOR_AZUL,
    COLOR_DORADO,
    COLOR_DORADO_OSCURO,
    BTN_RADIUS,
    FONT_UI,
    LOGO_FILE,
    ROL_ADMIN,
    DB_FILE,
)


def load_logo(size=(64, 64)):
    """
    Carga el logo desde LOGO_FILE en la carpeta del proyecto.
    Devuelve un CTkImage o None si falla.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, LOGO_FILE)
    if not os.path.exists(logo_path):
        return None

    try:
        img = Image.open(logo_path)
        img = img.resize(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


class NavBar(ctk.CTkFrame):
    """
    Barra de navegación horizontal superior con:
    - Logo + texto a la izquierda
    - Botones (Inicio, Productos, Almacenes, Usuarios)
    - Botón "Cerrar sesión" a la derecha
    """

    def __init__(self, parent, rol,
                 on_home, on_prod, on_alm, on_users, on_logout):
        super().__init__(parent, fg_color=COLOR_AZUL)

        # ----- Lado izquierdo: logo + texto -----
        left = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        left.pack(side="left", fill="y", padx=8)

        logo = load_logo((36, 36))
        if logo:
            lbl_logo = ctk.CTkLabel(left, image=logo, text="", fg_color=COLOR_AZUL)
            lbl_logo.image = logo
            lbl_logo.pack(side="left", padx=(4, 8), pady=4)

        ctk.CTkLabel(
            left,
            text="Inventario UNISON",
            font=("Segoe UI", 14, "bold"),
            text_color="white",
            fg_color=COLOR_AZUL
        ).pack(side="left", pady=4)

        # ----- Centro: botones de navegación -----
        center = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        center.pack(side="left", padx=16)

        def nav_button(text, command):
            return ctk.CTkButton(
                center, text=text, command=command,
                corner_radius=BTN_RADIUS,
                fg_color=COLOR_DORADO,
                hover_color=COLOR_DORADO_OSCURO,
                text_color="black", width=110, height=30
            )

        nav_button("Inicio", on_home).pack(side="left", padx=4, pady=6)
        nav_button("Productos", on_prod).pack(side="left", padx=4, pady=6)
        nav_button("Almacenes", on_alm).pack(side="left", padx=4, pady=6)

        # Usuarios solo si es ADMIN
        if (rol or "").upper() == ROL_ADMIN:
            nav_button("Usuarios", on_users).pack(side="left", padx=4, pady=6)

        # ----- Lado derecho: botón Cerrar sesión -----
        right = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        right.pack(side="right", padx=8)

        ctk.CTkButton(
            right, text="Cerrar sesión", command=on_logout,
            corner_radius=BTN_RADIUS,
            fg_color="#ef4444", hover_color="#dc2626",
            text_color="white", width=120, height=30
        ).pack(side="right", padx=4, pady=6)


def add_labeled_entry(parent, label_text, width=160):
    """
    Crea una sección:
      [Label]
      [Entry]
    y devuelve el Entry.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(side="top", fill="x", pady=2)

    ctk.CTkLabel(
        frame, text=label_text, font=("Segoe UI", 10),
        fg_color="transparent", text_color="#333"
    ).pack(side="top", anchor="w")

    entry = ctk.CTkEntry(
        frame, width=width, height=28,
        corner_radius=BTN_RADIUS, font=FONT_UI
    )
    entry.pack(side="top", anchor="w", pady=(0, 4))
    return entry


def add_labeled_date(parent, label_text, width=160):
    """
    Igual que add_labeled_entry, pero con placeholder 'YYYY-MM-DD'.
    Útil para filtros de fecha.
    """
    entry = add_labeled_entry(parent, label_text, width)
    entry.insert(0, "YYYY-MM-DD")
    entry.configure(text_color="#888")

    def on_focus_in(_event):
        if entry.get() == "YYYY-MM-DD":
            entry.delete(0, "end")
            entry.configure(text_color="black")

    def on_focus_out(_event):
        if not entry.get().strip():
            entry.delete(0, "end")
            entry.insert(0, "YYYY-MM-DD")
            entry.configure(text_color="#888")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    return entry


def safe_table_or_msg(parent, exists, table_name):
    """
    Si la tabla no existe, muestra un mensaje dentro del frame
    explicando que la tabla no está en la BD.
    Devuelve True si existe, False si no.
    """
    if exists:
        return True

    msg = ctk.CTkLabel(
        parent,
        text=(
            f"La tabla '{table_name}' no existe en la base de datos.\n"
            f"Revisa el archivo {DB_FILE}."
        ),
        font=("Segoe UI", 13),
        text_color="#b91c1c",
        fg_color="white",
        justify="center"
    )
    msg.pack(expand=True, padx=20, pady=20)
    return False
