# ==========================================
# views_usuarios.py
# Vista para ADMIN:
# - ver usuarios
# - cambiar rol
# - cambiar contraseña
# ==========================================

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import hashlib, secrets

from settings import (
    BTN_RADIUS, FONT_UI,
    COLOR_DORADO, COLOR_DORADO_OSCURO,
    ROL_ADMIN, ROL_PROD, ROL_ALM, ROL_VISIT
)
from db_utils import db, table_exists
from ui_widgets import safe_table_or_msg

ROLES_PERMITIDOS = (ROL_ADMIN, ROL_PROD, ROL_ALM, ROL_VISIT)


def _username_col(conn):
    """Detecta si la columna de nombre de usuario se llama 'nombre' o 'usuario'."""
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(usuarios)")]
    except Exception:
        cols = []
    if "nombre" in cols:
        return "nombre"
    if "usuario" in cols:
        return "usuario"
    return "nombre"


def _pack_password_sha256(plain: str) -> str:
    """Cifra contraseña en formato 'sha256$salt$hash'."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
    return f"sha256${salt}${h}"


class UsuariosView(ctk.CTkFrame):
    """Vista de administración de usuarios. Solo para ADMIN."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="white")
        self.editor_frame = None

        with db() as conn:
            existe = table_exists(conn, "usuarios")
        if not safe_table_or_msg(self, existe, "usuarios"):
            return

        ctk.CTkLabel(
            self,
            text="Gestión de Usuarios (solo ADMIN)",
            font=("Segoe UI", 13, "bold"), fg_color="white",
            text_color="#333"
        ).pack(anchor="w", padx=16, pady=(12, 4))

        # Tabla de usuarios
        table_frame = ctk.CTkFrame(self, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        self.cols = ("id", "usuario", "rol", "ultimo_inicio")
        headings = ("ID", "Usuario", "Rol", "Último inicio")
        widths = (50, 220, 140, 220)

        self.tree = ttk.Treeview(table_frame, columns=self.cols, show="headings", height=10)
        for c, h, w in zip(self.cols, headings, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        # Botones
        actions = ctk.CTkFrame(self, fg_color="white")
        actions.pack(fill="x", padx=16, pady=(0, 8))

        self.btn_rol = ctk.CTkButton(
            actions, text="Cambiar rol",
            corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
            text_color="black", width=140,
            command=self.start_change_role
        )
        self.btn_rol.pack(side="left", padx=4, pady=4)

        self.btn_pass = ctk.CTkButton(
            actions, text="Cambiar contraseña",
            corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
            text_color="black", width=180,
            command=self.start_change_password
        )
        self.btn_pass.pack(side="left", padx=4, pady=4)

        ctk.CTkButton(
            actions, text="Refrescar",
            corner_radius=BTN_RADIUS,
            fg_color="#e5e7eb", hover_color="#d1d5db",
            text_color="#333", width=120,
            command=self.load_data
        ).pack(side="left", padx=4, pady=4)

        ctk.CTkLabel(
            self,
            text="No se pueden crear ni eliminar usuarios aquí; solo modificar rol o contraseña.",
            font=("Segoe UI", 10), text_color="#666", fg_color="white"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self.load_data()

    def _selected(self):
        """Devuelve dict con datos del usuario seleccionado, o None."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Usuarios", "Selecciona un usuario de la tabla.")
            return None
        values = self.tree.item(sel[0])["values"]
        return {"id": values[0], "usuario": values[1], "rol": values[2]}

    def load_data(self):
        """Carga la tabla de usuarios desde la DB."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        with db() as conn:
            ucol = _username_col(conn)
            cols = [r[1] for r in conn.execute("PRAGMA table_info(usuarios)")]
            col_ult = "fecha_hora_ultimo_inicio" if "fecha_hora_ultimo_inicio" in cols else "NULL"
            sql = f"SELECT id, {ucol} AS usuario, rol, {col_ult} AS ultimo FROM usuarios ORDER BY id"
            for r in conn.execute(sql):
                self.tree.insert("", tk.END, values=r)

    def clear_editor(self):
        """Cierra panel de edición y reactiva botones."""
        if self.editor_frame is not None:
            self.editor_frame.destroy()
            self.editor_frame = None
        self.btn_rol.configure(state="normal")
        self.btn_pass.configure(state="normal")

    # --------- Cambiar rol ---------
    def start_change_role(self):
        row = self._selected()
        if not row:
            return
        self.show_role_editor(row)

    def show_role_editor(self, row):
        self.btn_rol.configure(state="disabled")
        self.btn_pass.configure(state="disabled")

        if self.editor_frame is not None:
            self.editor_frame.destroy()

        self.editor_frame = ctk.CTkFrame(self, fg_color="#f5f5f5", corner_radius=10)
        self.editor_frame.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            self.editor_frame,
            text=f"Cambiar rol — {row['usuario']}",
            font=("Segoe UI", 12, "bold"), fg_color="#f5f5f5"
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            self.editor_frame, text="Rol:", font=FONT_UI,
            fg_color="#f5f5f5"
        ).grid(row=1, column=0, sticky="e", padx=6, pady=6)

        self.opt_rol = ctk.CTkOptionMenu(
            self.editor_frame, values=list(ROLES_PERMITIDOS),
            width=220
        )
        self.opt_rol.set(row["rol"] or ROL_PROD)
        self.opt_rol.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        btns = ctk.CTkFrame(self.editor_frame, fg_color="#f5f5f5")
        btns.grid(row=2, column=0, columnspan=2, sticky="e", padx=10, pady=(8, 10))

        ctk.CTkButton(
            btns, text="Cancelar", corner_radius=BTN_RADIUS,
            fg_color="#e5e7eb", hover_color="#d1d5db", text_color="black",
            command=self.clear_editor
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btns, text="Guardar", corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
            text_color="black",
            command=lambda: self.save_role(row["id"])
        ).pack(side="right", padx=4)

    def save_role(self, user_id: int):
        new_role = self.opt_rol.get()
        if new_role not in ROLES_PERMITIDOS:
            messagebox.showerror("Usuarios", "Rol inválido.")
            return
        with db() as conn:
            conn.execute("UPDATE usuarios SET rol=? WHERE id=?", (new_role, user_id))
            conn.commit()
        self.clear_editor()
        self.load_data()

    # --------- Cambiar contraseña ---------
    def start_change_password(self):
        row = self._selected()
        if not row:
            return
        self.show_password_editor(row)

    def show_password_editor(self, row):
        self.btn_rol.configure(state="disabled")
        self.btn_pass.configure(state="disabled")

        if self.editor_frame is not None:
            self.editor_frame.destroy()

        self.editor_frame = ctk.CTkFrame(self, fg_color="#f5f5f5", corner_radius=10)
        self.editor_frame.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            self.editor_frame,
            text=f"Cambiar contraseña — {row['usuario']}",
            font=("Segoe UI", 12, "bold"), fg_color="#f5f5f5"
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            self.editor_frame, text="Nueva contraseña:",
            font=FONT_UI, fg_color="#f5f5f5"
        ).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.e_pass1 = ctk.CTkEntry(
            self.editor_frame, height=32, corner_radius=BTN_RADIUS,
            show="•", width=260, font=FONT_UI
        )
        self.e_pass1.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ctk.CTkLabel(
            self.editor_frame, text="Repetir contraseña:",
            font=FONT_UI, fg_color="#f5f5f5"
        ).grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.e_pass2 = ctk.CTkEntry(
            self.editor_frame, height=32, corner_radius=BTN_RADIUS,
            show="•", width=260, font=FONT_UI
        )
        self.e_pass2.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        btns = ctk.CTkFrame(self.editor_frame, fg_color="#f5f5f5")
        btns.grid(row=3, column=0, columnspan=2, sticky="e", padx=10, pady=(8, 10))

        ctk.CTkButton(
            btns, text="Cancelar", corner_radius=BTN_RADIUS,
            fg_color="#e5e7eb", hover_color="#d1d5db", text_color="black",
            command=self.clear_editor
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btns, text="Guardar", corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
            text_color="black",
            command=lambda: self.save_password(row["id"])
        ).pack(side="right", padx=4)

    def save_password(self, user_id: int):
        p1 = self.e_pass1.get().strip()
        p2 = self.e_pass2.get().strip()
        if not p1:
            messagebox.showwarning("Usuarios", "Ingresa una contraseña.")
            return
        if p1 != p2:
            messagebox.showwarning("Usuarios", "Las contraseñas no coinciden.")
            return

        packed = _pack_password_sha256(p1)
        with db() as conn:
            conn.execute("UPDATE usuarios SET password=? WHERE id=?", (packed, user_id))
            conn.commit()

        messagebox.showinfo("Usuarios", "Contraseña actualizada.")
        self.clear_editor()
        self.load_data()
