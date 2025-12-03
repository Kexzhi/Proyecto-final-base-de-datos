# ==========================================
# views_login.py
# Vista de inicio de sesión (Login)
# ==========================================

import customtkinter as ctk
from tkinter import messagebox

from settings import (
    COLOR_AZUL, COLOR_DORADO, COLOR_DORADO_OSCURO,
    BTN_RADIUS, FONT_UI
)
from db_utils import authenticate
from ui_widgets import load_logo


class LoginView(ctk.CTkFrame):
    """
    Vista de Login.
    Llama a on_ok(usuario, rol) cuando el inicio de sesión es correcto.
    """

    def __init__(self, parent, on_ok):
        # Fondo general azul, pero el contenido será mostly blanco
        super().__init__(parent, fg_color=COLOR_AZUL)
        self.on_ok = on_ok

        # ---------- Tarjeta central ----------
        card = ctk.CTkFrame(
            self,
            fg_color="white",
            corner_radius=20,
            width=520,
            height=420
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        # ---------- Zona superior: logo + títulos ----------
        header = ctk.CTkFrame(card, fg_color="white", corner_radius=20)
        header.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 0))

        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)

        # Logo más grande
        logo = load_logo((110, 110))
        if logo:
            lbl_logo = ctk.CTkLabel(header, image=logo, text="", fg_color="white")
            lbl_logo.image = logo
            lbl_logo.grid(row=0, column=0, padx=(24, 12), pady=18)

        title_frame = ctk.CTkFrame(header, fg_color="white")
        title_frame.grid(row=0, column=1, sticky="w", padx=(0, 24), pady=18)

        ctk.CTkLabel(
            title_frame,
            text="Sistema de Inventario",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_AZUL,
            fg_color="white",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Universidad de Sonora",
            font=("Segoe UI", 11),
            text_color="#555",
            fg_color="white",
        ).pack(anchor="w", pady=(2, 0))

        # Línea delgada de color dorado para separar
        ctk.CTkFrame(
            card,
            fg_color=COLOR_DORADO,
            height=2
        ).grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 4))

        # ---------- Cuerpo del formulario ----------
        body = ctk.CTkFrame(card, fg_color="white")
        body.grid(row=2, column=0, sticky="nsew", padx=26, pady=(10, 18))

        # Título "Inicio de sesión"
        ctk.CTkLabel(
            body,
            text="Inicio de sesión",
            font=("Segoe UI", 14, "bold"),
            text_color="#333",
            fg_color="white",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            body,
            text="Ingresa tu usuario y contraseña para acceder al sistema de inventario.",
            font=("Segoe UI", 10),
            text_color="#666",
            fg_color="white",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        # Campo usuario
        ctk.CTkLabel(
            body, text="Usuario", font=FONT_UI,
            text_color="#333", fg_color="white"
        ).pack(anchor="w", pady=(4, 0))

        self.ent_user = ctk.CTkEntry(
            body,
            width=380,
            height=32,
            corner_radius=BTN_RADIUS,
            font=FONT_UI,
        )
        self.ent_user.pack(anchor="w", pady=(2, 10))

        # Campo contraseña
        ctk.CTkLabel(
            body, text="Contraseña", font=FONT_UI,
            text_color="#333", fg_color="white"
        ).pack(anchor="w", pady=(4, 0))

        self.ent_pwd = ctk.CTkEntry(
            body,
            width=380,
            height=32,
            corner_radius=BTN_RADIUS,
            font=FONT_UI,
            show="•",
        )
        self.ent_pwd.pack(anchor="w", pady=(2, 16))

        # Botón iniciar sesión
        btn_login = ctk.CTkButton(
            body,
            text="Iniciar sesión",
            corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO,
            hover_color=COLOR_DORADO_OSCURO,
            text_color="black",
            width=190,
            height=34,
            command=self.try_login,
        )
        btn_login.pack(anchor="center", pady=(4, 0))

        # ⚠️ Importante: ya NO hay texto abajo con pistas de usuarios

        # ENTER en contraseña también hace login
        self.ent_pwd.bind("<Return>", lambda e: self.try_login())

        # Foco inicial en usuario
        self.ent_user.focus_set()

    # --------------------------------------
    # Lógica de login
    # --------------------------------------
    def try_login(self):
        """Lee los campos, valida y llama a authenticate()."""
        user = (self.ent_user.get() or "").strip()
        pwd = (self.ent_pwd.get() or "").strip()

        if not user or not pwd:
            messagebox.showwarning("Validación", "Ingresa usuario y contraseña.")
            return

        ok = authenticate(user, pwd)
        if not ok:
            messagebox.showerror("Acceso", "Usuario o contraseña incorrectos.")
            return

        _uid, nombre, rol = ok
        self.on_ok(nombre, rol)
