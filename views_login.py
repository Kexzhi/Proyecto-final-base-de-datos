# views_login.py
# -----------------------------------------
# Vista de inicio de sesión:
# - tarjeta centrada
# - logo grande
# - validación contra la BD
# -----------------------------------------

import customtkinter as ctk
from tkinter import messagebox

from settings import (
    COLOR_AZUL,
    COLOR_DORADO,
    COLOR_DORADO_OSCURO,
    BTN_RADIUS,
    FONT_UI,
)
from ui_widgets import load_logo
from db_utils import authenticate_user


class LoginView(ctk.CTkFrame):
    """
    Pantalla de login.
    Recibe un callback on_ok(usuario, rol) que se llama sólo si el login es correcto.
    """

    def __init__(self, parent, on_ok):
        super().__init__(parent, fg_color=COLOR_AZUL)
        self.on_ok = on_ok

        # ---------- Tarjeta blanca centrada ----------
        card = ctk.CTkFrame(
            self,
            fg_color="white",
            corner_radius=18,
            width=420,
            height=420,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(card, fg_color="white")
        inner.pack(expand=True, fill="both", padx=32, pady=24)

        # ---------- Logo ----------
        logo = load_logo((110, 110))
        if logo:
            lbl_logo = ctk.CTkLabel(inner, image=logo, text="", fg_color="white")
            lbl_logo.image = logo
            lbl_logo.pack(pady=(0, 8))

        # ---------- Títulos ----------
        ctk.CTkLabel(
            inner,
            text="Sistema de Inventario",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_AZUL,
            fg_color="white",
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            inner,
            text="Universidad de Sonora",
            font=("Segoe UI", 12),
            text_color="#555",
            fg_color="white",
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text="Inicio de sesión",
            font=("Segoe UI", 13, "bold"),
            text_color="#111",
            fg_color="white",
        ).pack(pady=(6, 4), anchor="w")

        # ---------- Campo Usuario ----------
        user_frame = ctk.CTkFrame(inner, fg_color="white")
        user_frame.pack(fill="x", pady=(4, 4))

        ctk.CTkLabel(
            user_frame,
            text="Usuario",
            font=("Segoe UI", 10),
            text_color="#333",
            fg_color="white",
        ).pack(anchor="w")

        self.ent_user = ctk.CTkEntry(
            user_frame,
            height=32,
            corner_radius=BTN_RADIUS,
            font=FONT_UI,
        )
        self.ent_user.pack(fill="x", pady=(2, 4))

        # ---------- Campo Contraseña ----------
        pass_frame = ctk.CTkFrame(inner, fg_color="white")
        pass_frame.pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(
            pass_frame,
            text="Contraseña",
            font=("Segoe UI", 10),
            text_color="#333",
            fg_color="white",
        ).pack(anchor="w")

        self.ent_pass = ctk.CTkEntry(
            pass_frame,
            height=32,
            corner_radius=BTN_RADIUS,
            font=FONT_UI,
            show="*",
        )
        self.ent_pass.pack(fill="x", pady=(2, 4))

        # ---------- Botón Iniciar sesión ----------
        self.btn_login = ctk.CTkButton(
            inner,
            text="Iniciar sesión",
            command=self._do_login,
            corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO,
            hover_color=COLOR_DORADO_OSCURO,
            text_color="black",
            height=36,
        )
        self.btn_login.pack(fill="x", pady=(16, 4))

        # Enter para aceptar
        self.ent_pass.bind("<Return>", lambda _e: self._do_login())
        self.ent_user.bind("<Return>", lambda _e: self._do_login())

        # focus inicial en usuario
        self.ent_user.focus_set()

    # ---------- Lógica de login ----------

    def _do_login(self):
        """Lee usuario/contraseña, pregunta a la BD y llama on_ok si es correcto."""
        user = self.ent_user.get()
        pwd = self.ent_pass.get()

        ok, nombre, rol, msg = authenticate_user(user, pwd)

        if not ok:
            messagebox.showerror("Acceso", msg)
            return

        if callable(self.on_ok):
            self.on_ok(nombre, rol)
