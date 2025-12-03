# ==========================================
# views_productos.py
# Vista de productos:
# - filtros en sidebar izquierdo (colapsable)
# - tabla central
# - panel embebido para agregar/modificar (solo ADMIN/PRODUCTOS)
# - VISITANTE solo puede ver y filtrar
# ==========================================

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from settings import (
    BTN_RADIUS, FONT_UI,
    COLOR_DORADO, COLOR_DORADO_OSCURO,
    ROL_ADMIN, ROL_PROD, ROL_VISIT
)
from db_utils import db, table_exists, touch_audit
from ui_widgets import add_labeled_entry, add_labeled_date, safe_table_or_msg


# ------------------------------------------
# Info dinámica de columnas de productos
# ------------------------------------------
def _productos_cols_info():
    """
    Devuelve un diccionario con las columnas actuales de 'productos':
      { nombre_col: {notnull: bool, dflt: valor_defecto} }
    Esto sirve para adaptarnos al esquema real de la BD.
    """
    info = {}
    with db() as conn:
        try:
            for cid, name, ctype, notnull, dflt, pk in conn.execute("PRAGMA table_info(productos)"):
                info[name] = {"notnull": bool(notnull), "dflt": dflt}
        except Exception:
            pass
    return info


class ProductosView(ctk.CTkFrame):
    """Vista principal de Productos."""

    def __init__(self, parent, usuario: str, rol: str):
        super().__init__(parent, fg_color="white")
        self.usuario = usuario
        self.rol = (rol or "").upper()
        self.editor_frame = None
        self.editing_id = None

        # Comprobamos existencia de tabla productos
        with db() as conn:
            existe = table_exists(conn, "productos")
        if not safe_table_or_msg(self, existe, "productos"):
            return

        # Info de columnas para adaptarnos al esquema real
        self.cols_info = _productos_cols_info()
        self.has_cant = "cantidad" in self.cols_info
        self.has_almid = "almacen_id" in self.cols_info
        self.has_depto = "departamento" in self.cols_info
        self.depto_notnull = self.cols_info.get("departamento", {}).get("notnull", False)

        # ---------- LAYOUT: SIDEBAR (filtros) + MAIN (tabla) ----------
        wrapper = ctk.CTkFrame(self, fg_color="white")
        wrapper.pack(fill="both", expand=True)

        # Sidebar de filtros
        sidebar = ctk.CTkFrame(wrapper, fg_color="#f4f4f4", corner_radius=0)
        sidebar.pack(side="left", fill="y", padx=(0, 4), pady=0)

        ctk.CTkLabel(
            sidebar, text="Filtros de Productos",
            font=("Segoe UI", 12, "bold"), text_color="#333",
            fg_color="#f4f4f4"
        ).pack(anchor="w", padx=10, pady=(10, 4))

        self.sidebar_visible = True

        def toggle_sidebar():
            """Oculta o muestra el panel de filtros."""
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

        # --- Campos de filtro ---
        self.f_nombre = add_labeled_entry(sidebar, "Nombre contiene")

        if self.has_depto:
            self.f_depto = add_labeled_entry(sidebar, "Departamento contiene")
        else:
            self.f_depto = None

        self.f_precio_min = add_labeled_entry(sidebar, "Precio mín.")
        self.f_precio_max = add_labeled_entry(sidebar, "Precio máx.")

        if self.has_cant:
            self.f_cant_min = add_labeled_entry(sidebar, "Cantidad mín.")
            self.f_cant_max = add_labeled_entry(sidebar, "Cantidad máx.")
        else:
            self.f_cant_min = self.f_cant_max = None

        self.f_fecha_desde = add_labeled_date(sidebar, "Creado desde")
        self.f_fecha_hasta = add_labeled_date(sidebar, "Creado hasta")

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

        cols = ["id", "nombre", "precio"]
        headers = ["ID", "Nombre", "Precio"]
        widths = [60, 220, 90]

        if self.has_cant:
            cols.append("cantidad"); headers.append("Cantidad"); widths.append(90)
        if self.has_depto:
            cols.append("departamento"); headers.append("Departamento"); widths.append(130)
        if self.has_almid:
            cols.append("almacen"); headers.append("Almacén"); widths.append(140)

        cols += ["creado", "ult_mod", "ult_usuario"]
        headers += ["Creado", "Últ. Mod.", "Últ. Usuario"]
        widths += [150, 150, 160]

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        # Botones de acción (solo ADMIN/PRODUCTOS)
        actions = ctk.CTkFrame(main_area, fg_color="white")
        actions.pack(fill="x", padx=4, pady=(0, 4))

        can_edit = self.rol in (ROL_ADMIN, ROL_PROD)
        state = "normal" if can_edit else "disabled"

        self.btn_add = ctk.CTkButton(
            actions, text="Agregar",
            corner_radius=BTN_RADIUS, width=120,
            fg_color=COLOR_DORADO if can_edit else "#ddd",
            hover_color=COLOR_DORADO_OSCURO, text_color="black",
            state=state, command=self.start_add
        )
        self.btn_add.pack(side="left", padx=4, pady=4)

        self.btn_edit = ctk.CTkButton(
            actions, text="Modificar",
            corner_radius=BTN_RADIUS, width=120,
            fg_color=COLOR_DORADO if can_edit else "#ddd",
            hover_color=COLOR_DORADO_OSCURO, text_color="black",
            state=state, command=self.start_edit
        )
        self.btn_edit.pack(side="left", padx=4, pady=4)

        self.btn_del = ctk.CTkButton(
            actions, text="Eliminar",
            corner_radius=BTN_RADIUS, width=120,
            fg_color="#ef4444" if can_edit else "#ddd",
            hover_color="#dc2626", text_color="white",
            state=state, command=self.delete_selected
        )
        self.btn_del.pack(side="left", padx=4, pady=4)

        # Donde se coloca el panel de edición embebido
        self.editor_container = main_area

        # Carga inicial de datos
        self.load_data()

    # --------------------------------------
    # Construir SQL con filtros
    # --------------------------------------
    def _build_query(self):
        """
        Construye la consulta SELECT a productos
        aplicando todos los filtros activos.
        """
        select = ["p.id", "p.nombre", "p.precio"]
        if self.has_cant:
            select.append("p.cantidad")
        if self.has_depto:
            select.append("p.departamento")

        join = ""
        if self.has_almid:
            # Unimos con almacenes para mostrar el nombre, no solo el ID
            join = "LEFT JOIN almacenes a ON a.id=p.almacen_id"
            select.append("COALESCE(a.nombre,'-') AS almacen")

        select += [
            "p.fecha_hora_creacion",
            "p.fecha_hora_ultima_modificacion",
            "p.ultimo_usuario_en_modificar"
        ]

        sql = f"SELECT {', '.join(select)} FROM productos p {join} WHERE 1=1"
        params = []

        # --- Filtro por nombre ---
        v = self.f_nombre.get().strip()
        if v:
            sql += " AND p.nombre LIKE ?"
            params.append(f"%{v}%")

        # --- Filtro por departamento ---
        if self.has_depto and self.f_depto:
            v = self.f_depto.get().strip()
            if v:
                sql += " AND p.departamento LIKE ?"
                params.append(f"%{v}%")

        # Helper para números
        def num(x: str):
            try:
                return float(x)
            except:
                return None

        # --- Rangos de precio ---
        v = num(self.f_precio_min.get().strip())
        if v is not None:
            sql += " AND p.precio>=?"
            params.append(v)

        v = num(self.f_precio_max.get().strip())
        if v is not None:
            sql += " AND p.precio<=?"
            params.append(v)

        # --- Rangos de cantidad ---
        if self.has_cant and self.f_cant_min:
            v = num(self.f_cant_min.get().strip())
            if v is not None:
                sql += " AND p.cantidad>=?"
                params.append(v)

        if self.has_cant and self.f_cant_max:
            v = num(self.f_cant_max.get().strip())
            if v is not None:
                sql += " AND p.cantidad<=?"
                params.append(v)

        # --- Rangos de fecha de creación ---
        fd = self.f_fecha_desde.get().strip()
        if fd and fd != "YYYY-MM-DD":
            sql += " AND date(p.fecha_hora_creacion) >= date(?)"
            params.append(fd)

        fh = self.f_fecha_hasta.get().strip()
        if fh and fh != "YYYY-MM-DD":
            sql += " AND date(p.fecha_hora_creacion) <= date(?)"
            params.append(fh)

        sql += " ORDER BY p.id DESC"
        return sql, params

    # --------------------------------------
    # Cargar datos
    # --------------------------------------
    def load_data(self):
        """Vacía y vuelve a llenar la tabla según filtros."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        with db() as conn:
            try:
                sql, params = self._build_query()
                for row in conn.execute(sql, params).fetchall():
                    self.tree.insert("", tk.END, values=row)
            except Exception as e:
                messagebox.showerror("DB", f"Error consultando productos:\n{e}")

    # --------------------------------------
    # Manejo del panel de edición
    # --------------------------------------
    def clear_editor(self):
        """Cierra el panel de edición y reactiva botones según rol."""
        if self.editor_frame is not None:
            self.editor_frame.destroy()
            self.editor_frame = None
        self.editing_id = None

        can_edit = self.rol in (ROL_ADMIN, ROL_PROD)
        state = "normal" if can_edit else "disabled"

        self.btn_add.configure(state=state, fg_color=COLOR_DORADO if can_edit else "#ddd")
        self.btn_edit.configure(state=state, fg_color=COLOR_DORADO if can_edit else "#ddd")
        self.btn_del.configure(state=state, fg_color="#ef4444" if can_edit else "#ddd")

    def start_add(self):
        """Inicia modo 'Agregar producto'."""
        self.show_editor(product_id=None)

    def start_edit(self):
        """Inicia modo 'Modificar producto' con el producto seleccionado."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Productos", "Selecciona un producto para modificar.")
            return
        pid = self.tree.item(sel[0])["values"][0]
        self.show_editor(product_id=pid)

    def show_editor(self, product_id: int | None):
        """
        Crea el formulario de agregar/modificar como un panel
        dentro de la misma vista (no abre una nueva ventana).
        """
        self.btn_add.configure(state="disabled")
        self.btn_edit.configure(state="disabled")
        self.btn_del.configure(state="disabled")

        if self.editor_frame is not None:
            self.editor_frame.destroy()

        self.editor_frame = ctk.CTkFrame(self.editor_container, fg_color="#f5f5f5", corner_radius=10)
        self.editor_frame.pack(fill="x", padx=4, pady=(0, 8))

        titulo = "Agregar producto" if product_id is None else f"Modificar producto (ID {product_id})"
        ctk.CTkLabel(
            self.editor_frame, text=titulo,
            font=("Segoe UI", 12, "bold"), fg_color="#f5f5f5"
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 4))

        # Campos de formulario
        ctk.CTkLabel(self.editor_frame, text="Nombre:", font=FONT_UI, fg_color="#f5f5f5") \
            .grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.e_nombre = ctk.CTkEntry(self.editor_frame, width=260, height=30,
                                     corner_radius=BTN_RADIUS, font=FONT_UI)
        self.e_nombre.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ctk.CTkLabel(self.editor_frame, text="Precio:", font=FONT_UI, fg_color="#f5f5f5") \
            .grid(row=1, column=2, sticky="e", padx=6, pady=4)
        self.e_precio = ctk.CTkEntry(self.editor_frame, width=140, height=30,
                                     corner_radius=BTN_RADIUS, font=FONT_UI)
        self.e_precio.grid(row=1, column=3, sticky="w", padx=6, pady=4)

        if self.has_cant:
            ctk.CTkLabel(self.editor_frame, text="Cantidad:", font=FONT_UI, fg_color="#f5f5f5") \
                .grid(row=2, column=0, sticky="e", padx=6, pady=4)
            self.e_cant = ctk.CTkEntry(self.editor_frame, width=140, height=30,
                                       corner_radius=BTN_RADIUS, font=FONT_UI)
            self.e_cant.grid(row=2, column=1, sticky="w", padx=6, pady=4)
        else:
            self.e_cant = None

        if self.has_almid:
            ctk.CTkLabel(self.editor_frame, text="Almacén ID:", font=FONT_UI, fg_color="#f5f5f5") \
                .grid(row=2, column=2, sticky="e", padx=6, pady=4)
            self.e_almid = ctk.CTkEntry(self.editor_frame, width=140, height=30,
                                        corner_radius=BTN_RADIUS, font=FONT_UI)
            self.e_almid.grid(row=2, column=3, sticky="w", padx=6, pady=4)
        else:
            self.e_almid = None

        if self.has_depto:
            label = "Departamento:"
            if self.depto_notnull:
                label += " *"
            ctk.CTkLabel(self.editor_frame, text=label, font=FONT_UI, fg_color="#f5f5f5") \
                .grid(row=3, column=0, sticky="e", padx=6, pady=4)
            self.e_depto = ctk.CTkEntry(self.editor_frame, width=260, height=30,
                                        corner_radius=BTN_RADIUS, font=FONT_UI)
            self.e_depto.grid(row=3, column=1, sticky="w", padx=6, pady=4)
        else:
            self.e_depto = None

        # Botones Guardar / Cancelar
        btns = ctk.CTkFrame(self.editor_frame, fg_color="#f5f5f5")
        btns.grid(row=4, column=0, columnspan=4, sticky="e", padx=10, pady=(8, 10))

        ctk.CTkButton(
            btns, text="Cancelar", corner_radius=BTN_RADIUS,
            fg_color="#e5e7eb", hover_color="#d1d5db", text_color="black",
            command=self.clear_editor
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btns, text="Guardar", corner_radius=BTN_RADIUS,
            fg_color=COLOR_DORADO, hover_color=COLOR_DORADO_OSCURO, text_color="black",
            command=self.save_editor
        ).pack(side="right", padx=4)

        self.editing_id = product_id

        # Si es edición, cargamos datos
        if product_id is not None:
            self._load_product_into_editor(product_id)

    def _load_product_into_editor(self, product_id: int):
        """Carga datos de un producto existente al formulario."""
        with db() as conn:
            row = conn.execute("SELECT * FROM productos WHERE id=?", (product_id,)).fetchone()
            if not row:
                messagebox.showerror("Productos", "No se encontró el producto.")
                self.clear_editor()
                return

            cols = [c[1] for c in conn.execute("PRAGMA table_info(productos)")]
            def val(col):
                return row[cols.index(col)] if col in cols else ""

            self.e_nombre.insert(0, str(val("nombre") or ""))
            self.e_precio.insert(0, str(val("precio") or ""))
            if self.e_cant is not None:
                self.e_cant.insert(0, str(val("cantidad") or ""))
            if self.e_almid is not None:
                self.e_almid.insert(0, str(val("almacen_id") or ""))
            if self.e_depto is not None:
                self.e_depto.insert(0, str(val("departamento") or ""))

    # --------------------------------------
    # Guardar producto
    # --------------------------------------
    def save_editor(self):
        """Valida y guarda (insert o update) el producto."""
        import sqlite3

        nombre = (self.e_nombre.get() if self.e_nombre else "").strip()
        if not nombre:
            messagebox.showwarning("Validación", "Ingresa un nombre.")
            return

        try:
            precio = float((self.e_precio.get() if self.e_precio else "").strip())
        except:
            messagebox.showwarning("Validación", "Precio inválido.")
            return

        cant = (self.e_cant.get().strip() if self.e_cant else None)
        alm = (self.e_almid.get().strip() if self.e_almid else None)
        depto = (self.e_depto.get().strip() if self.e_depto else None)

        if self.has_depto and self.depto_notnull and not depto:
            messagebox.showwarning("Validación", "El campo Departamento es obligatorio.")
            return

        try:
            with db() as conn:
                if self.editing_id is not None:
                    # UPDATE
                    sets, params = ["nombre=?", "precio=?"], [nombre, precio]
                    if self.has_cant and self.e_cant and cant not in (None, ""):
                        sets.append("cantidad=?"); params.append(float(cant))
                    if self.has_almid and self.e_almid and alm not in (None, ""):
                        sets.append("almacen_id=?"); params.append(int(alm))
                    if self.has_depto and self.e_depto:
                        sets.append("departamento=?"); params.append(depto or "")

                    params.append(self.editing_id)
                    conn.execute(
                        f"UPDATE productos SET {', '.join(sets)} WHERE id=?",
                        params
                    )
                    touch_audit(conn, "productos", self.usuario, self.editing_id)
                else:
                    # INSERT
                    fields, qmarks, params = ["nombre", "precio"], ["?", "?"], [nombre, precio]
                    if self.has_cant and self.e_cant and cant not in (None, ""):
                        fields.append("cantidad"); qmarks.append("?"); params.append(float(cant))
                    if self.has_almid and self.e_almid and alm not in (None, ""):
                        fields.append("almacen_id"); qmarks.append("?"); params.append(int(alm))
                    if self.has_depto and self.e_depto:
                        fields.append("departamento"); qmarks.append("?"); params.append(depto or "")

                    fields.append("fecha_hora_creacion"); qmarks.append("datetime('now')")

                    conn.execute(
                        f"INSERT INTO productos({', '.join(fields)}) VALUES ({', '.join(qmarks)})",
                        params
                    )

                conn.commit()

            messagebox.showinfo("Producto", "Guardado correctamente.")
            self.clear_editor()
            self.load_data()

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Base de datos", f"No se pudo guardar (integridad):\n{e}")
        except Exception as e:
            messagebox.showerror("Base de datos", f"Error guardando el producto:\n{e}")

    # --------------------------------------
    # Eliminar
    # --------------------------------------
    def delete_selected(self):
        """Elimina producto (solo ADMIN/PRODUCTOS). VISITANTE no puede."""
        if self.rol not in (ROL_ADMIN, ROL_PROD):
            return
        sel = self.tree.selection()
        if not sel:
            return
        pid = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar producto ID {pid}?"):
            with db() as conn:
                conn.execute("DELETE FROM productos WHERE id=?", (pid,))
                conn.commit()
            self.load_data()
