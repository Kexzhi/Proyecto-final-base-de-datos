"""
Vista de Productos

- Tabla con los productos del inventario.
- Filtros en un panel lateral (se puede ocultar/mostrar).
- Formulario inline (dentro de la misma ventana) para Agregar/Editar.
- Botones Agregar / Editar / Eliminar visibles solo para roles:
  ADMIN y PRODUCTOS.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

import customtkinter as ctk
from tkinter import ttk, messagebox

from settings import (
    DB_FILE,
    COLOR_AZUL,
    COLOR_DORADO,
    FONT_UI,
    ROL_ADMIN,
    ROL_PROD,
)


# ---------------------------------------------------------------------------
# Utilidades de BD
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    """Abre conexión a la BD con filas tipo diccionario."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def listar_nombres_almacenes() -> List[str]:
    """Devuelve lista de nombres de almacenes (para filtros y combo)."""
    with get_conn() as conn:
        cur = conn.execute("SELECT nombre FROM almacenes ORDER BY nombre")
        return [r["nombre"] for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Formulario inline para productos
# ---------------------------------------------------------------------------

class ProductoFormInline(ctk.CTkFrame):
    """
    Formulario embebido (sin ventana aparte) para crear o editar productos.

    - Si product_row es None => modo "Nuevo producto".
    - Si product_row tiene datos => modo "Editar producto".
    - Cuando el usuario pulsa Guardar, se llama a on_save(data_dict).
    """

    def __init__(
            self,
            parent,
            almacenes: List[str],
            usuario: str,
            product_row: Optional[sqlite3.Row],
            on_save,
            on_cancel,
    ):
        super().__init__(parent, fg_color="#f7f7f7", corner_radius=10)
        self.almacenes = almacenes
        self.usuario = usuario
        self.product_row = product_row
        self.on_save = on_save
        self.on_cancel = on_cancel

        # Layout base: columnas para etiquetas/campos
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        titulo = "Nuevo producto" if product_row is None else "Editar producto"
        ctk.CTkLabel(
            self,
            text=titulo,
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_AZUL,
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 4))

        fila = 1

        # Nombre
        ctk.CTkLabel(self, text="Nombre:", font=FONT_UI).grid(
            row=fila, column=0, sticky="e", padx=5, pady=3
        )
        self.ent_nombre = ctk.CTkEntry(self, width=220)
        self.ent_nombre.grid(row=fila, column=1, sticky="w", padx=5, pady=3)

        # Precio
        ctk.CTkLabel(self, text="Precio:", font=FONT_UI).grid(
            row=fila, column=2, sticky="e", padx=5, pady=3
        )
        self.ent_precio = ctk.CTkEntry(self, width=120)
        self.ent_precio.grid(row=fila, column=3, sticky="w", padx=5, pady=3)
        fila += 1

        # Cantidad
        ctk.CTkLabel(self, text="Cantidad:", font=FONT_UI).grid(
            row=fila, column=0, sticky="e", padx=5, pady=3
        )
        self.ent_cantidad = ctk.CTkEntry(self, width=120)
        self.ent_cantidad.grid(row=fila, column=1, sticky="w", padx=5, pady=3)

        # Departamento
        ctk.CTkLabel(self, text="Departamento:", font=FONT_UI).grid(
            row=fila, column=2, sticky="e", padx=5, pady=3
        )
        self.ent_depto = ctk.CTkEntry(self, width=220)
        self.ent_depto.grid(row=fila, column=3, sticky="w", padx=5, pady=3)
        fila += 1

        # Almacén (texto, pero elegido de una lista válida)
        ctk.CTkLabel(self, text="Almacén:", font=FONT_UI).grid(
            row=fila, column=0, sticky="e", padx=5, pady=3
        )
        self.cb_almacen = ctk.CTkComboBox(
            self,
            width=220,
            values=[""] + almacenes,
            state="readonly",
        )
        self.cb_almacen.grid(row=fila, column=1, sticky="w", padx=5, pady=3)

        # Botones
        btn_guardar = ctk.CTkButton(
            self,
            text="Guardar",
            fg_color=COLOR_DORADO,
            hover_color="#d99d00",
            command=self._on_guardar,
            width=100,
        )
        btn_guardar.grid(row=fila, column=2, sticky="e", padx=5, pady=10)

        btn_cancelar = ctk.CTkButton(
            self,
            text="Cancelar",
            fg_color="#bdc3c7",
            text_color="black",
            hover_color="#95a5a6",
            command=self._on_cancelar,
            width=100,
        )
        btn_cancelar.grid(row=fila, column=3, sticky="w", padx=5, pady=10)

        # Si estamos en modo edición, precargar datos
        if self.product_row is not None:
            self._cargar_datos()

    def _cargar_datos(self):
        r = self.product_row
        self.ent_nombre.insert(0, r["nombre"])
        self.ent_precio.insert(0, str(r["precio"]))
        self.ent_cantidad.insert(0, str(r["cantidad"]))
        self.ent_depto.insert(0, r["departamento"] or "")
        if r["almacen"]:
            self.cb_almacen.set(r["almacen"])

    def _on_guardar(self):
        nombre = self.ent_nombre.get().strip()
        precio_txt = self.ent_precio.get().strip()
        cant_txt = self.ent_cantidad.get().strip()
        depto = self.ent_depto.get().strip()
        alm = self.cb_almacen.get().strip()

        if not nombre:
            messagebox.showerror("Validación", "El nombre es obligatorio.", parent=self)
            return

        if not depto:
            messagebox.showerror("Validación", "El departamento es obligatorio.", parent=self)
            return

        try:
            precio = float(precio_txt)
        except ValueError:
            messagebox.showerror("Validación", "El precio debe ser numérico.", parent=self)
            return

        try:
            cantidad = int(cant_txt)
        except ValueError:
            messagebox.showerror("Validación", "La cantidad debe ser entera.", parent=self)
            return

        if alm and alm not in self.almacenes:
            messagebox.showerror(
                "Validación",
                "Selecciona un almacén válido de la lista.",
                parent=self,
            )
            return

        data = {
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "departamento": depto,
            "almacen": alm if alm else None,
            "usuario": self.usuario,
        }

        if self.on_save:
            self.on_save(data)

    def _on_cancelar(self):
        if self.on_cancel:
            self.on_cancel()
# ---------------------------------------------------------------------------
# Vista principal de productos
# ---------------------------------------------------------------------------

class ProductosView(ctk.CTkFrame):
    """
    Vista principal de productos.

    parent  -> contenedor (viene del App)
    usuario -> nombre de usuario logueado
    rol     -> rol ("ADMIN", "PRODUCTOS", etc.)
    """

    def __init__(self, parent, usuario: str, rol: str):
        super().__init__(parent, fg_color="white")
        self.usuario = usuario
        self.rol = rol

        # Nombres de almacenes válidos
        try:
            self.almacenes = listar_nombres_almacenes()
        except Exception:
            self.almacenes = []

        # Formulario inline (se crea/borra cuando se usa)
        self.form_inline: Optional[ProductoFormInline] = None

        # Layout general
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # ----- Encabezado (título + botones de acciones) -----
        header = ctk.CTkFrame(self, fg_color="white")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Gestión de productos",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_AZUL,
        ).pack(side="left")

        if self.rol in (ROL_ADMIN, ROL_PROD):
            btn_add = ctk.CTkButton(
                header,
                text="Agregar",
                fg_color=COLOR_DORADO,
                hover_color="#d99d00",
                width=90,
                command=self._mostrar_form_nuevo,
            )
            btn_add.pack(side="right", padx=5)

            btn_del = ctk.CTkButton(
                header,
                text="Eliminar",
                fg_color="#c0392b",
                hover_color="#922b21",
                width=90,
                command=self._eliminar_producto,
            )
            btn_del.pack(side="right", padx=5)

            btn_edit = ctk.CTkButton(
                header,
                text="Editar",
                fg_color="#2980b9",
                hover_color="#21618c",
                width=90,
                command=self._mostrar_form_editar,
            )
            btn_edit.pack(side="right", padx=5)

        # ----- Contenedor para el formulario inline -----
        self.form_container = ctk.CTkFrame(self, fg_color="white")
        self.form_container.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        # ----- Cuerpo: filtros + tabla -----
        body = ctk.CTkFrame(self, fg_color="white")
        body.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Panel lateral de filtros (fijo a la izquierda)
        self.frame_filtros = ctk.CTkFrame(body, fg_color="#f3f6fb", corner_radius=12)
        self.frame_filtros.grid(row=0, column=0, sticky="nsw", padx=(0, 8), pady=5)

        self._crear_panel_filtros(self.frame_filtros)

        # Botón para ocultar/mostrar filtros
        self.filtros_visibles = True
        btn_toggle = ctk.CTkButton(
            body,
            text="Ocultar filtros",
            width=110,
            fg_color="#cccccc",
            text_color="black",
            command=lambda: self._toggle_filtros(btn_toggle),
        )
        btn_toggle.grid(row=1, column=0, sticky="w", pady=(0, 5))

        # Tabla
        frame_tabla = ctk.CTkFrame(body, fg_color="white")
        frame_tabla.grid(row=0, column=1, rowspan=2, sticky="nsew")
        frame_tabla.rowconfigure(0, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        self._crear_tabla(frame_tabla)

        # Carga inicial
        self._load_data()

    # ------------------------------------------------------------------
    # Panel de filtros
    # ------------------------------------------------------------------

    def _crear_panel_filtros(self, parent):
        ctk.CTkLabel(
            parent,
            text="Filtros de búsqueda",
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 10), sticky="w")

        fila = 1

        # Nombre contiene
        ctk.CTkLabel(parent, text="Nombre contiene:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        self.f_nombre = ctk.CTkEntry(parent, width=180)
        self.f_nombre.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        # Departamento
        ctk.CTkLabel(parent, text="Departamento:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        self.f_depto = ctk.CTkEntry(parent, width=180)
        self.f_depto.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        # Precio
        ctk.CTkLabel(parent, text="Precio mínimo:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        self.f_pmin = ctk.CTkEntry(parent, width=80)
        self.f_pmin.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        ctk.CTkLabel(parent, text="Precio máximo:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        self.f_pmax = ctk.CTkEntry(parent, width=80)
        self.f_pmax.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        # Cantidad
        ctk.CTkLabel(parent, text="Cant. mínima:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        self.f_cmin = ctk.CTkEntry(parent, width=80)
        self.f_cmin.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        ctk.CTkLabel(parent, text="Cant. máxima:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        self.f_cmax = ctk.CTkEntry(parent, width=80)
        self.f_cmax.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        # Almacén
        ctk.CTkLabel(parent, text="Almacén:", font=FONT_UI).grid(
            row=fila, column=0, sticky="w", padx=10
        )
        valores_alm = ["(Todos)"] + self.almacenes
        self.f_almacen = ctk.CTkComboBox(
            parent, width=180, values=valores_alm, state="readonly"
        )
        self.f_almacen.set("(Todos)")
        self.f_almacen.grid(row=fila, column=1, sticky="w", padx=10, pady=3)
        fila += 1

        # Botones filtros
        btn_aplicar = ctk.CTkButton(
            parent,
            text="Aplicar filtros",
            fg_color=COLOR_AZUL,
            hover_color="#003c73",
            width=120,
            command=self._load_data,
        )
        btn_aplicar.grid(row=fila, column=0, padx=10, pady=(10, 10), sticky="w")

        btn_limpiar = ctk.CTkButton(
            parent,
            text="Limpiar",
            fg_color="#bdc3c7",
            text_color="black",
            hover_color="#95a5a6",
            width=80,
            command=self._limpiar_filtros,
        )
        btn_limpiar.grid(row=fila, column=1, padx=10, pady=(10, 10), sticky="w")

    def _toggle_filtros(self, boton):
        if self.filtros_visibles:
            self.frame_filtros.grid_remove()
            boton.configure(text="Mostrar filtros")
            self.filtros_visibles = False
        else:
            self.frame_filtros.grid()
            boton.configure(text="Ocultar filtros")
            self.filtros_visibles = True

    def _limpiar_filtros(self):
        for entry in (self.f_nombre, self.f_depto,
                      self.f_pmin, self.f_pmax,
                      self.f_cmin, self.f_cmax):
            entry.delete(0, "end")
        self.f_almacen.set("(Todos)")
        self._load_data()

    # ------------------------------------------------------------------
    # Tabla
    # ------------------------------------------------------------------

    def _crear_tabla(self, parent):
        cols = (
            "id",
            "nombre",
            "precio",
            "cantidad",
            "departamento",
            "almacen",
            "creado",
            "modificado",
            "usuario",
        )
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("precio", text="Precio")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("departamento", text="Departamento")
        self.tree.heading("almacen", text="Almacén")
        self.tree.heading("creado", text="Creado")
        self.tree.heading("modificado", text="Últ. Mod.")
        self.tree.heading("usuario", text="Usuario Mod.")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nombre", width=160)
        self.tree.column("precio", width=80, anchor="e")
        self.tree.column("cantidad", width=80, anchor="e")
        self.tree.column("departamento", width=120)
        self.tree.column("almacen", width=120)
        self.tree.column("creado", width=140)
        self.tree.column("modificado", width=140)
        self.tree.column("usuario", width=120)

        sb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        if self.rol in (ROL_ADMIN, ROL_PROD):
            self.tree.bind("<Double-1>", lambda e: self._mostrar_form_editar())

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def _build_where(self):
        where = " WHERE 1=1"
        params = []

        nombre = self.f_nombre.get().strip()
        depto = self.f_depto.get().strip()
        pmin = self.f_pmin.get().strip()
        pmax = self.f_pmax.get().strip()
        cmin = self.f_cmin.get().strip()
        cmax = self.f_cmax.get().strip()
        alm = self.f_almacen.get().strip()

        if nombre:
            where += " AND nombre LIKE ?"
            params.append(f"%{nombre}%")

        if depto:
            where += " AND departamento LIKE ?"
            params.append(f"%{depto}%")

        if pmin:
            try:
                float(pmin)
                where += " AND precio >= ?"
                params.append(pmin)
            except ValueError:
                pass

        if pmax:
            try:
                float(pmax)
                where += " AND precio <= ?"
                params.append(pmax)
            except ValueError:
                pass

        if cmin:
            try:
                int(cmin)
                where += " AND cantidad >= ?"
                params.append(cmin)
            except ValueError:
                pass

        if cmax:
            try:
                int(cmax)
                where += " AND cantidad <= ?"
                params.append(cmax)
            except ValueError:
                pass

        if alm and alm != "(Todos)":
            where += " AND almacen = ?"
            params.append(alm)

        return where, params

    def _load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        where, params = self._build_where()
        sql = f"""
            SELECT
                id,
                nombre,
                precio,
                cantidad,
                departamento,
                almacen,
                fecha_hora_creacion,
                fecha_hora_ultima_modificacion,
                ultimo_usuario_en_modificar
            FROM productos
            {where}
            ORDER BY id
        """

        try:
            with get_conn() as conn:
                cur = conn.execute(sql, params)
                for r in cur.fetchall():
                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            r["id"],
                            r["nombre"],
                            r["precio"],
                            r["cantidad"],
                            r["departamento"],
                            r["almacen"],
                            r["fecha_hora_creacion"],
                            r["fecha_hora_ultima_modificacion"],
                            r["ultimo_usuario_en_modificar"],
                        ),
                    )
        except Exception as e:
            messagebox.showerror(
                "Error en BD",
                f"No se pudieron cargar los productos:\n{e}",
                parent=self,
            )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _get_id_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0])["values"]
        return vals[0] if vals else None

    def _ocultar_form(self):
        if self.form_inline is not None:
            self.form_inline.destroy()
            self.form_inline = None

    def _mostrar_form_nuevo(self):
        if self.rol not in (ROL_ADMIN, ROL_PROD):
            return

        self._ocultar_form()

        def on_save(data):
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with get_conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO productos
                        (nombre, precio, cantidad, departamento,
                         almacen,
                         fecha_hora_creacion,
                         fecha_hora_ultima_modificacion,
                         ultimo_usuario_en_modificar)
                        VALUES (?,?,?,?,?,?,?,?)
                        """,
                        (
                            data["nombre"],
                            data["precio"],
                            data["cantidad"],
                            data["departamento"],
                            data["almacen"],
                            now,
                            now,
                            data["usuario"],
                        ),
                    )
                self._ocultar_form()
                self._load_data()
            except Exception as e:
                messagebox.showerror(
                    "Error en BD",
                    f"No se pudo guardar el producto:\n{e}",
                    parent=self,
                )

        self.form_inline = ProductoFormInline(
            self.form_container,
            self.almacenes,
            self.usuario,
            product_row=None,
            on_save=on_save,
            on_cancel=self._ocultar_form,
        )
        self.form_inline.pack(fill="x", padx=0, pady=(0, 5))

    def _mostrar_form_editar(self):
        if self.rol not in (ROL_ADMIN, ROL_PROD):
            return

        prod_id = self._get_id_seleccionado()
        if prod_id is None:
            messagebox.showinfo(
                "Editar producto",
                "Selecciona un producto primero.",
                parent=self,
            )
            return

        try:
            with get_conn() as conn:
                cur = conn.execute("SELECT * FROM productos WHERE id = ?", (prod_id,))
                row = cur.fetchone()
                if row is None:
                    messagebox.showerror(
                        "Editar producto",
                        "El producto ya no existe.",
                        parent=self,
                    )
                    return
        except Exception as e:
            messagebox.showerror(
                "Error en BD",
                f"No se pudo leer el producto:\n{e}",
                parent=self,
            )
            return

        self._ocultar_form()

        def on_save(data):
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with get_conn() as conn:
                    conn.execute(
                        """
                        UPDATE productos
                        SET nombre = ?,
                            precio = ?,
                            cantidad = ?,
                            departamento = ?,
                            almacen = ?,
                            fecha_hora_ultima_modificacion = ?,
                            ultimo_usuario_en_modificar = ?
                        WHERE id = ?
                        """,
                        (
                            data["nombre"],
                            data["precio"],
                            data["cantidad"],
                            data["departamento"],
                            data["almacen"],
                            now,
                            data["usuario"],
                            prod_id,
                        ),
                    )
                self._ocultar_form()
                self._load_data()
            except Exception as e:
                messagebox.showerror(
                    "Error en BD",
                    f"No se pudo actualizar el producto:\n{e}",
                    parent=self,
                )

        self.form_inline = ProductoFormInline(
            self.form_container,
            self.almacenes,
            self.usuario,
            product_row=row,
            on_save=on_save,
            on_cancel=self._ocultar_form,
        )
        self.form_inline.pack(fill="x", padx=0, pady=(0, 5))

    def _eliminar_producto(self):
        if self.rol not in (ROL_ADMIN, ROL_PROD):
            return

        prod_id = self._get_id_seleccionado()
        if prod_id is None:
            messagebox.showinfo(
                "Eliminar producto",
                "Selecciona un producto primero.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Seguro que deseas eliminar el producto #{prod_id}?",
                parent=self,
        ):
            return

        try:
            with get_conn() as conn:
                conn.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
            self._load_data()
        except Exception as e:
            messagebox.showerror(
                "Error en BD",
                f"No se pudo eliminar el producto:\n{e}",
                parent=self,
            )
