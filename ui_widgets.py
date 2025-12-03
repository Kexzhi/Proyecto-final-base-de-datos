# ==========================================
# ui_widgets.py
# Widgets reutilizables:
# - Logo UNISON
# - Barra de navegación (NavBar)
# - Entradas con etiqueta
# - Mensaje si falta tabla
# ==========================================

import os
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from settings import (
    COLOR_AZUL, COLOR_DORADO, COLOR_DORADO_OSCURO,
    FONT_UI, BTN_RADIUS, LOGO_FILE, ROL_ADMIN
)


# ------------------------------------------
# Cargar logo UNISON
# ------------------------------------------
def load_logo(size=(36, 36)):
    """
    Intenta cargar el logo desde LOGO_FILE.
    Devuelve un CTkImage o None si no se encuentra o falla.
    """
    path = os.path.join(os.path.dirname(__file__), LOGO_FILE)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path)
        img = img.resize(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


# ------------------------------------------
# Barra superior de navegación
# ------------------------------------------
class NavBar(ctk.CTkFrame):
    """
    Barra superior con:
      - logo + título
      - botones: Inicio, Productos, Almacenes, (Usuarios si ADMIN)
      - botón "Cerrar sesión"
    """

    def __init__(self, parent, on_home, on_prod, on_alm, on_users, on_logout, rol: str):
        super().__init__(parent, fg_color=COLOR_AZUL)

        # Lado izquierdo: logo + texto
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

        # Centro: botones de navegación
        center = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        center.pack(side="left", padx=16)

        def nav_button(text, command):
            return ctk.CTkButton(
                center, text=text, command=command,
                corner_radius=BTN_RADIUS,
                fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
                text_color="black", width=110, height=30
            )

        nav_button("Inicio", on_home).pack(side="left", padx=4, pady=6)
        nav_button("Productos", on_prod).pack(side="left", padx=4, pady=6)
        nav_button("Almacenes", on_alm).pack(side="left", padx=4, pady=6)

        # Usuarios solo si es ADMIN
        if (rol or "").upper() == ROL_ADMIN:
            nav_button("Usuarios", on_users).pack(side="left", padx=4, pady=6)

        # Lado derecho: botón Cerrar sesión
        right = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        right.pack(side="right", padx=8)

        ctk.CTkButton(
            right, text="Cerrar sesión", command=on_logout,
            corner_radius=BTN_RADIUS,
            fg_color="#ef4444", hover_color="#dc2626",
            text_color="white", width=120, height=30
        ).pack(side="right", padx=4, pady=6)


# ------------------------------------------
# Entradas con etiqueta
# ------------------------------------------
def add_labeled_entry(parent, label_text: str, width=160):
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


def add_labeled_date(parent, label_text: str, width=160):
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
            entry.insert(0, "YYYY-MM-DD")
            entry.configure(text_color="#888")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    return entry


# ------------------------------------------
# Mensaje si falta tabla
# ------------------------------------------
def safe_table_or_msg(parent, exists: bool, table_name: str) -> bool:
    """
    Si la tabla no existe:
      - muestra un messagebox de error
      - coloca un label en la vista
    Devuelve True si existe, False si no.
    """
    if not exists:
        messagebox.showerror(
            "Base de datos",
            f"La tabla '{table_name}' no existe en la base de datos."
        )
        ctk.CTkLabel(
            parent, text=f"No se puede mostrar la tabla '{table_name}'.",
            font=("Segoe UI", 12), text_color="red"
        ).pack(pady=20)
        return False
    return True
