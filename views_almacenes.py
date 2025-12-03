# views_almacenes.py
import customtkinter as ctk
from tkinter import ttk, messagebox

from settings import COLOR_AZUL, COLOR_DORADO, FONT_UI, ROL_ADMIN, ROL_ALM
from db_utils import list_almacenes, create_almacen, update_almacen, delete_almacen


class AlmacenesView(ctk.CTkFrame):
    """
    Vista de ALMACENES.

    - Panel lateral de filtros (mostrar/ocultar) que siempre se queda en el mismo lado.
    - Tabla central con los almacenes.
    - Formulario inferior para Agregar / Editar sin ventana extra.
    """

    def __init__(self, parent, usuario: str, rol: str):
        super().__init__(parent, fg_color="white")
        self.usuario = usuario
        self.rol = rol
        self._selected_id: int | None = None

        self._build_layout()
        self._load_data()

    # ---------- Construcción de interfaz ----------

    def _build_layout(self) -> None:
        # Usamos grid para que el panel lateral NO mueva la tabla
        self.columnconfigure(0, weight=0)   # filtros
        self.columnconfigure(1, weight=1)   # tabla + editor
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # --- Panel de filtros (col 0) ---
        self.filters_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        self.filters_frame.grid(row=0, column=0, sticky="nsew")
        self._build_filters(self.filters_frame)

        # --- Botón para mostrar/ocultar filtros ---
        top_tools = ctk.CTkFrame(self, fg_color="white")
        top_tools.grid(row=0, column=1, sticky="ew")
        top_tools.columnconfigure(0, weight=0)
        top_tools.columnconfigure(1, weight=1)

        self.btn_toggle_filters = ctk.CTkButton(
            top_tools,
            text="Ocultar filtros",
            fg_color=COLOR_AZUL,
            hover_color="#003b73",
            text_color="white",
            font=FONT_UI,
            command=self._toggle_filters,
            corner_radius=16,
            width=130,
        )
        self.btn_toggle_filters.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # --- Permisos para botones CRUD ---
        self.puede_editar = self.rol in (ROL_ADMIN, ROL_ALM)

        # Contenedor para tabla + editor
        content = ctk.CTkFrame(self, fg_color="white")
        content.grid(row=0, column=1, sticky="nsew", pady=(45, 0))  # deja espacio para barra arriba
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=0)
        content.columnconfigure(0, weight=1)

        # Tabla
        self.tree = ttk.Treeview(
            content,
            columns=("id", "nombre", "creado", "modificado", "ultimo"),
            show="headings",
            height=12,
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("creado", text="Creado")
        self.tree.heading("modificado", text="Últ. Mod.")
        self.tree.heading("ultimo", text="Último usuario")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nombre", width=200, anchor="w")
        self.tree.column("creado", width=150, anchor="center")
        self.tree.column("modificado", width=150, anchor="center")
        self.tree.column("ultimo", width=150, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 5))

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Scroll
        scrollbar = ttk.Scrollbar(
            content, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=(0, 5))

        # Editor inferior (inline)
        self.editor = ctk.CTkFrame(content, fg_color="#f9f9f9")
        self.editor.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self._build_editor(self.editor)

    def _build_filters(self, frame: ctk.CTkFrame) -> None:
        frame.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text="Filtros",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_AZUL,
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(
            frame, text="Nombre contiene:", font=FONT_UI
        ).grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")

        self.f_nombre = ctk.CTkEntry(frame, font=FONT_UI, width=160)
        self.f_nombre.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")

        btn_aplicar = ctk.CTkButton(
            frame,
            text="Aplicar filtros",
            fg_color=COLOR_DORADO,
            hover_color="#e0a600",
            text_color="black",
            font=FONT_UI,
            command=self._load_data,
            corner_radius=16,
        )
        btn_aplicar.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        btn_limpiar = ctk.CTkButton(
            frame,
            text="Limpiar filtros",
            fg_color="#cccccc",
            hover_color="#bbbbbb",
            text_color="black",
            font=FONT_UI,
            command=self._clear_filters,
            corner_radius=16,
        )
        btn_limpiar.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

    def _build_editor(self, frame: ctk.CTkFrame) -> None:
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)

        ctk.CTkLabel(
            frame, text="Editor de almacén", font=("Segoe UI", 13, "bold")
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(5, 5), sticky="w")

        ctk.CTkLabel(frame, text="Nombre:", font=FONT_UI).grid(
            row=1, column=0, padx=10, pady=(5, 0), sticky="e"
        )
        self.e_nombre = ctk.CTkEntry(frame, font=FONT_UI)
        self.e_nombre.grid(row=1, column=1, padx=10, pady=(5, 0), sticky="ew")

        # Botones CRUD
        self.btn_nuevo = ctk.CTkButton(
            frame,
            text="Nuevo",
            fg_color=COLOR_DORADO,
            hover_color="#e0a600",
            text_color="black",
            font=FONT_UI,
            corner_radius=16,
            command=self._nuevo,
        )
        self.btn_guardar = ctk.CTkButton(
            frame,
            text="Guardar",
            fg_color=COLOR_AZUL,
            hover_color="#003b73",
            text_color="white",
            font=FONT_UI,
            corner_radius=16,
            command=self._guardar,
        )
        self.btn_eliminar = ctk.CTkButton(
            frame,
            text="Eliminar",
            fg_color="#d9534f",
            hover_color="#c9302c",
            text_color="white",
            font=FONT_UI,
            corner_radius=16,
            command=self._eliminar,
        )

        col_btns = 2
        self.btn_nuevo.grid(row=1, column=col_btns, padx=5, pady=(5, 0), sticky="ew")
        self.btn_guardar.grid(row=1, column=col_btns + 1, padx=5, pady=(5, 0), sticky="ew")
        self.btn_eliminar.grid(row=1, column=col_btns + 2, padx=5, pady=(5, 0), sticky="ew")

        # Permisos
        if not self.puede_editar:
            self.btn_nuevo.configure(state="disabled")
            self.btn_guardar.configure(state="disabled")
            self.btn_eliminar.configure(state="disabled")
            self.e_nombre.configure(state="disabled")

    # ---------- Filtros ----------

    def _toggle_filters(self) -> None:
        if self.filters_frame.winfo_ismapped():
            # Ocultar sin cambiar el grid de la tabla
            self.filters_frame.grid_remove()
            self.btn_toggle_filters.configure(text="Mostrar filtros")
        else:
            self.filters_frame.grid()
            self.btn_toggle_filters.configure(text="Ocultar filtros")

    def _clear_filters(self) -> None:
        self.f_nombre.delete(0, "end")
        self._load_data()

    # ---------- Carga de datos ----------

    def _load_data(self) -> None:
        nombre_like = self.f_nombre.get().strip() or None

        try:
            rows = list_almacenes(nombre_like=nombre_like)
        except Exception as e:
            messagebox.showerror("Error en BD", f"No se pudieron cargar los almacenes:\n{e}")
            return

        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["nombre"],
                    row["fecha_hora_creacion"] or "",
                    row["fecha_hora_ultima_modificacion"] or "",
                    row["ultimo_usuario_en_modificar"] or "",
                ),
            )

        # limpiar selección/editor
        self._selected_id = None
        self.e_nombre.delete(0, "end")

    # ---------- Editor inline ----------

    def _on_tree_select(self, event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        vals = item["values"]
        if not vals:
            return
        self._selected_id = int(vals[0])
        nombre = vals[1]

        self.e_nombre.configure(state="normal")
        self.e_nombre.delete(0, "end")
        self.e_nombre.insert(0, nombre)

    def _nuevo(self) -> None:
        """Limpia el editor para crear un nuevo almacén."""
        self._selected_id = None
        self.e_nombre.configure(state="normal")
        self.e_nombre.delete(0, "end")
        self.e_nombre.focus()

    def _guardar(self) -> None:
        if not self.puede_editar:
            return

        nombre = self.e_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Validación", "El nombre del almacén es obligatorio.")
            return

        try:
            if self._selected_id is None:
                create_almacen(nombre, self.usuario)
            else:
                update_almacen(self._selected_id, nombre, self.usuario)
        except Exception as e:
            messagebox.showerror("Error en BD", f"No se pudo guardar el almacén:\n{e}")
            return

        self._load_data()

    def _eliminar(self) -> None:
        if not self.puede_editar:
            return
        if self._selected_id is None:
            messagebox.showinfo("Eliminar", "Selecciona un almacén primero.")
            return

        if not messagebox.askyesno(
                "Confirmar eliminación",
                "¿Seguro que deseas eliminar este almacén?"
        ):
            return

        try:
            delete_almacen(self._selected_id)
        except Exception as e:
            messagebox.showerror("Error en BD", f"No se pudo eliminar el almacén:\n{e}")
            return

        self._load_data()
