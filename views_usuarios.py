# views_usuarios.py
import customtkinter as ctk
from tkinter import ttk, messagebox

from settings import (
    COLOR_AZUL,
    COLOR_DORADO,
    FONT_UI,
    ROL_ADMIN,
    ROL_PROD,
    ROL_ALM,
    ROL_VIS,
)
from db_utils import list_users, create_user, update_user, delete_user


ROLES_PERMITIDOS = (ROL_ADMIN, ROL_PROD, ROL_ALM, ROL_VIS)


class UsuariosView(ctk.CTkFrame):
    """
    Vista de USUARIOS.

    - Solo el rol ADMIN puede crear/editar/eliminar.
    - Editor inline (sin ventana emergente).
    """

    def __init__(self, parent, usuario: str, rol: str):
        super().__init__(parent, fg_color="white")
        self.usuario = usuario
        self.rol = rol
        self._selected_id: int | None = None

        self.puede_editar = self.rol == ROL_ADMIN

        self._build_layout()
        self._load_data()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # Tabla
        table_frame = ctk.CTkFrame(self, fg_color="white")
        table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "nombre", "rol", "ultimo_inicio"),
            show="headings",
            height=12,
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("ultimo_inicio", text="Último inicio")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nombre", width=160, anchor="w")
        self.tree.column("rol", width=110, anchor="center")
        self.tree.column("ultimo_inicio", width=180, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Editor
        editor = ctk.CTkFrame(self, fg_color="#f9f9f9")
        editor.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        editor.columnconfigure(1, weight=1)
        editor.columnconfigure(3, weight=1)

        ctk.CTkLabel(
            editor, text="Editor de usuario", font=("Segoe UI", 13, "bold")
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(5, 5), sticky="w")

        # Nombre
        ctk.CTkLabel(editor, text="Nombre:", font=FONT_UI).grid(
            row=1, column=0, padx=10, pady=(5, 0), sticky="e"
        )
        self.e_nombre = ctk.CTkEntry(editor, font=FONT_UI)
        self.e_nombre.grid(row=1, column=1, padx=10, pady=(5, 0), sticky="ew")

        # Password
        ctk.CTkLabel(editor, text="Contraseña:", font=FONT_UI).grid(
            row=2, column=0, padx=10, pady=(5, 0), sticky="e"
        )
        self.e_password = ctk.CTkEntry(editor, font=FONT_UI, show="*")
        self.e_password.grid(row=2, column=1, padx=10, pady=(5, 0), sticky="ew")

        # Rol
        ctk.CTkLabel(editor, text="Rol:", font=FONT_UI).grid(
            row=1, column=2, padx=10, pady=(5, 0), sticky="e"
        )
        self.e_rol = ctk.CTkComboBox(
            editor,
            values=list(ROLES_PERMITIDOS),
            font=FONT_UI,
            state="readonly",
            width=130,
        )
        self.e_rol.set(ROL_VIS)

        self.e_rol.grid(row=1, column=3, padx=10, pady=(5, 0), sticky="ew")

        # Botones
        self.btn_nuevo = ctk.CTkButton(
            editor,
            text="Nuevo",
            fg_color=COLOR_DORADO,
            hover_color="#e0a600",
            text_color="black",
            font=FONT_UI,
            corner_radius=16,
            command=self._nuevo,
        )
        self.btn_guardar = ctk.CTkButton(
            editor,
            text="Guardar",
            fg_color=COLOR_AZUL,
            hover_color="#003b73",
            text_color="white",
            font=FONT_UI,
            corner_radius=16,
            command=self._guardar,
        )
        self.btn_eliminar = ctk.CTkButton(
            editor,
            text="Eliminar",
            fg_color="#d9534f",
            hover_color="#c9302c",
            text_color="white",
            font=FONT_UI,
            corner_radius=16,
            command=self._eliminar,
        )

        self.btn_nuevo.grid(row=3, column=1, padx=5, pady=10, sticky="ew")
        self.btn_guardar.grid(row=3, column=2, padx=5, pady=10, sticky="ew")
        self.btn_eliminar.grid(row=3, column=3, padx=5, pady=10, sticky="ew")

        if not self.puede_editar:
            # Deshabilitamos todo si NO es admin
            for w in (
                    self.e_nombre,
                    self.e_password,
                    self.e_rol,
                    self.btn_nuevo,
                    self.btn_guardar,
                    self.btn_eliminar,
            ):
                w.configure(state="disabled")

    # ---------- Datos ----------

    def _load_data(self) -> None:
        try:
            rows = list_users()
        except Exception as e:
            messagebox.showerror("Error en BD", f"No se pudieron cargar los usuarios:\n{e}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["nombre"],
                    row["rol"],
                    row["fecha_hora_ultimo_inicio"] or "",
                ),
            )

        self._selected_id = None
        self.e_nombre.delete(0, "end")
        self.e_password.delete(0, "end")
        self.e_rol.set(ROL_VIS)

    # ---------- Editor ----------

    def _on_tree_select(self, event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return

        self._selected_id = int(vals[0])
        nombre = vals[1]
        rol = vals[2]

        self.e_nombre.configure(state="normal")
        self.e_password.configure(state="normal")
        self.e_rol.configure(state="readonly")

        self.e_nombre.delete(0, "end")
        self.e_nombre.insert(0, nombre)
        self.e_password.delete(0, "end")  # no mostramos el hash, se deja en blanco
        if rol in ROLES_PERMITIDOS:
            self.e_rol.set(rol)
        else:
            self.e_rol.set(ROL_VIS)

    def _nuevo(self) -> None:
        self._selected_id = None
        self.e_nombre.configure(state="normal")
        self.e_password.configure(state="normal")
        self.e_rol.configure(state="readonly")

        self.e_nombre.delete(0, "end")
        self.e_password.delete(0, "end")
        self.e_rol.set(ROL_VIS)
        self.e_nombre.focus()

    def _guardar(self) -> None:
        if not self.puede_editar:
            return

        nombre = self.e_nombre.get().strip()
        pw = self.e_password.get().strip()
        rol = self.e_rol.get().strip()

        if not nombre:
            messagebox.showwarning("Validación", "El nombre es obligatorio.")
            return
        if rol not in ROLES_PERMITIDOS:
            messagebox.showwarning("Validación", "Selecciona un rol válido.")
            return

        try:
            if self._selected_id is None:
                if not pw:
                    messagebox.showwarning(
                        "Validación",
                        "Para crear un usuario nuevo se requiere contraseña.",
                    )
                    return
                create_user(nombre, pw, rol)
            else:
                # Si la contraseña está vacía, mantenemos la actual
                pw_final = pw or None
                update_user(self._selected_id, nombre, pw_final, rol)
        except Exception as e:
            messagebox.showerror("Error en BD", f"No se pudo guardar el usuario:\n{e}")
            return

        self._load_data()

    def _eliminar(self) -> None:
        if not self.puede_editar:
            return

        if self._selected_id is None:
            messagebox.showinfo("Eliminar", "Selecciona un usuario primero.")
            return

        if not messagebox.askyesno(
                "Confirmar eliminación",
                "¿Seguro que deseas eliminar este usuario?",
        ):
            return

        try:
            delete_user(self._selected_id)
        except Exception as e:
            messagebox.showerror("Error en BD", f"No se pudo eliminar el usuario:\n{e}")
            return

        self._load_data()
