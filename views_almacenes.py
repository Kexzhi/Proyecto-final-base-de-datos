# ==========================================
# views_almacenes.py
# Vista de almacenes:
# - filtros en sidebar
# - tabla
# - panel embebido para CRUD (solo ADMIN/ALMACENES)
# ==========================================

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from settings import (
    BTN_RADIUS, FONT_UI,
    COLOR_DORADO, COLOR_DORADO_OSCURO,
    ROL_ADMIN, ROL_ALM, ROL_VISIT
)
from db_utils import db, table_exists, touch_audit
from ui_widgets import add_labeled_entry, add_labeled_date, safe_table_or_msg


class AlmacenesView(ctk.CTkFrame):
    """Vista principal para administrar almacenes."""

    def __init__(self, parent, usuario: str, rol: str):
        super().__init__(parent, fg_color="white")
        self.usuario = usuario
        self.rol = (rol or "").upper()
        self.editor_frame = None
        self.editing_id = None

        with db() as conn:
            existe = table_exists(conn, "almacenes")
        if not safe_table_or_msg(self, existe, "almacenes"):
            return

        wrapper = ctk.CTkFrame(self, fg_color="white")
        wrapper.pack(fill="both", expand=True)

        # Sidebar de filtros
        sidebar = ctk.CTkFrame(wrapper, fg_color="#f4f4f4", corner_radius=0)
        sidebar.pack(side="left", fill="y", padx=(0, 4), pady=0)

        ctk.CTkLabel(
            sidebar, text="Filtros de Almacenes",
            font=("Segoe UI", 12, "bold"), text_color="#333",
            fg_color="#f4f4f4"
        ).pack(anchor="w", padx=10, pady=(10, 4))

        self.sidebar_visible = True

        def toggle_sidebar():
            if self.sidebar_visible:
                sidebar.pack_forget()
                self.sidebar_visible = False
            else:
                sidebar.pack(side="left", fill="y", padx=(0, 4), pady=0)
                self.sidebar_visible = True

        ctk.CTkButton(
            sidebar, text="Ocultar/mostrar filtros",
            corner_radius=BTN_RADIUS,
            fg_color="#e5e7eb", hover_color="#d1d5db",
            text_color="#333", width=160, height=28,
            command=toggle_sidebar
        ).pack(padx=10, pady=(0, 8))

        self.f_nom = add_labeled_entry(sidebar, "Nombre contiene")
        self.f_fd = add_labeled_date(sidebar, "Creado desde")
        self.f_fh = add_labeled_date(sidebar, "Creado hasta")

        ctk.CTkButton(
            sidebar, text="Aplicar filtros",
            corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
            text_color="black", width=160, height=32,
            command=self.load_data
        ).pack(padx=10, pady=(6, 10))

        # Área principal
        main_area = ctk.CTkFrame(wrapper, fg_color="white")
        main_area.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        # Tabla
        table_frame = ctk.CTkFrame(main_area, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=4, pady=4)

        cols = ("id", "nombre", "creado", "ult_mod", "ult_usuario")
        headers = ("ID", "Nombre", "Creado", "Últ. Mod.", "Últ. Usuario")
        widths = (60, 260, 180, 180, 180)

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        # Botones de acción
        actions = ctk.CTkFrame(main_area, fg_color="white")
        actions.pack(fill="x", padx=4, pady=(0, 4))

        can_edit = self.rol in (ROL_ADMIN, ROL_ALM)
        state = "normal" if can_edit else "disabled"

        self.btn_add = ctk.CTkButton(
            actions, text="Agregar", corner_radius=BTN_RADIUS, width=120,
            fg_color=COLOR_DORADO if can_edit else "#ddd",
            hover_color=COLOR_DORADO_OSCURO, text_color="black",
            state=state, command=self.start_add
        )
        self.btn_add.pack(side="left", padx=4, pady=4)

        self.btn_edit = ctk.CTkButton(
            actions, text="Modificar", corner_radius=BTN_RADIUS, width=120,
            fg_color=COLOR_DORADO if can_edit else "#ddd",
            hover_color=COLOR_DORADO_OSCURO, text_color="black",
            state=state, command=self.start_edit
        )
        self.btn_edit.pack(side="left", padx=4, pady=4)

        self.btn_del = ctk.CTkButton(
            actions, text="Eliminar", corner_radius=BTN_RADIUS, width=120,
            fg_color="#ef4444" if can_edit else "#ddd",
            hover_color="#dc2626", text_color="white",
            state=state, command=self.delete_selected
        )
        self.btn_del.pack(side="left", padx=4, pady=4)

        self.editor_container = main_area
        self.load_data()

    def _build_query(self):
        sql = (
            "SELECT id, nombre, fecha_hora_creacion, "
            "fecha_hora_ultima_modificacion, ultimo_usuario_en_modificar "
            "FROM almacenes WHERE 1=1"
        )
        params = []

        if (v := self.f_nom.get().strip()):
            sql += " AND nombre LIKE ?"; params.append(f"%{v}%")

        fd = self.f_fd.get().strip()
        if fd and fd != "YYYY-MM-DD":
            sql += " AND date(fecha_hora_creacion) >= date(?)"; params.append(fd)

        fh = self.f_fh.get().strip()
        if fh and fh != "YYYY-MM-DD":
            sql += " AND date(fecha_hora_creacion) <= date(?)"; params.append(fh)

        sql += " ORDER BY id DESC"
        return sql, params

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        with db() as conn:
            try:
                sql, params = self._build_query()
                for row in conn.execute(sql, params).fetchall():
                    self.tree.insert("", tk.END, values=row)
            except Exception as e:
                messagebox.showerror("DB", f"Error consultando almacenes:\n{e}")

    def clear_editor(self):
        if self.editor_frame is not None:
            self.editor_frame.destroy()
            self.editor_frame = None
        self.editing_id = None

        can_edit = self.rol in (ROL_ADMIN, ROL_ALM)
        state = "normal" if can_edit else "disabled"

        self.btn_add.configure(state=state, fg_color=COLOR_DORADO if can_edit else "#ddd")
        self.btn_edit.configure(state=state, fg_color=COLOR_DORADO if can_edit else "#ddd")
        self.btn_del.configure(state=state, fg_color="#ef4444" if can_edit else "#ddd")

    def start_add(self):
        self.show_editor(almacen_id=None)

    def start_edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Almacenes", "Selecciona un almacén para modificar.")
            return
        aid = self.tree.item(sel[0])["values"][0]
        self.show_editor(almacen_id=aid)

    def show_editor(self, almacen_id: int | None):
        self.btn_add.configure(state="disabled")
        self.btn_edit.configure(state="disabled")
        self.btn_del.configure(state="disabled")

        if self.editor_frame is not None:
            self.editor_frame.destroy()

        self.editor_frame = ctk.CTkFrame(self.editor_container, fg_color="#f5f5f5", corner_radius=10)
        self.editor_frame.pack(fill="x", padx=4, pady=(0, 8))

        titulo = "Agregar almacén" if almacen_id is None else f"Modificar almacén (ID {almacen_id})"
        ctk.CTkLabel(
            self.editor_frame, text=titulo,
            font=("Segoe UI", 12, "bold"), fg_color="#f5f5f5"
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(self.editor_frame, text="Nombre:", font=FONT_UI, fg_color="#f5f5f5") \
            .grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.e_nombre = ctk.CTkEntry(self.editor_frame, width=320, height=30,
                                     corner_radius=BTN_RADIUS, font=FONT_UI)
        self.e_nombre.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        btns = ctk.CTkFrame(self.editor_frame, fg_color="#f5f5f5")
        btns.grid(row=2, column=0, columnspan=3, sticky="e", padx=10, pady=(8, 10))

        ctk.CTkButton(
            btns, text="Cancelar", corner_radius=BTN_RADIUS,
            fg_color="#e5e7eb", hover_color="#d1d5db", text_color="black",
            command=self.clear_editor
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btns, text="Guardar", corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO,
            text_color="black", command=self.save_editor
        ).pack(side="right", padx=4)

        self.editing_id = almacen_id

        if almacen_id is not None:
            with db() as conn:
                row = conn.execute("SELECT nombre FROM almacenes WHERE id=?", (almacen_id,)).fetchone()
                if row:
                    self.e_nombre.insert(0, str(row[0] or ""))

    def save_editor(self):
        import sqlite3

        nombre = self.e_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Validación", "Ingresa un nombre.")
            return

        try:
            with db() as conn:
                if self.editing_id is not None:
                    conn.execute(
                        "UPDATE almacenes SET nombre=? WHERE id=?",
                        (nombre, self.editing_id)
                    )
                    touch_audit(conn, "almacenes", self.usuario, self.editing_id)
                else:
                    conn.execute(
                        "INSERT INTO almacenes(nombre, fecha_hora_creacion) "
                        "VALUES (?, datetime('now'))",
                        (nombre,)
                    )
                conn.commit()

            messagebox.showinfo("Almacén", "Guardado correctamente.")
            self.clear_editor()
            self.load_data()

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Base de datos", f"No se pudo guardar (integridad):\n{e}")
        except Exception as e:
            messagebox.showerror("Base de datos", f"Error guardando el almacén:\n{e}")

    def delete_selected(self):
        if self.rol not in (ROL_ADMIN, ROL_ALM):
            return
        sel = self.tree.selection()
        if not sel:
            return
        aid = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar almacén ID {aid}?"):
            with db() as conn:
                conn.execute("DELETE FROM almacenes WHERE id=?", (aid,))
                conn.commit()
            self.load_data()
