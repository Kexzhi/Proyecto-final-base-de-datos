# main.py
# -----------------------------------------
# Punto de entrada de la aplicación:
# - configura la ventana principal
# - muestra login, luego la vista Inicio
# - navegación entre Productos, Almacenes, Usuarios
# -----------------------------------------

import customtkinter as ctk
from tkinter import messagebox

from settings import COLOR_AZUL, COLOR_FONDO, ROL_ADMIN
from db_utils import ensure_schema_and_seed_users
from ui_widgets import NavBar, load_logo
from views_login import LoginView
from views_productos import ProductosView
from views_almacenes import AlmacenesView
from views_usuarios import UsuariosView


class HomeView(ctk.CTkFrame):
    """Vista de inicio (bienvenida) después del login."""

    def __init__(self, parent, usuario, rol):
        super().__init__(parent, fg_color="white")
        self.usuario = usuario
        self.rol = rol

        wrapper = ctk.CTkFrame(self, fg_color="white")
        wrapper.pack(expand=True)

        logo = load_logo((180, 180))
        if logo:
            lbl_logo = ctk.CTkLabel(wrapper, image=logo, text="", fg_color="white")
            lbl_logo.image = logo
            lbl_logo.pack(pady=(30, 10))

        ctk.CTkLabel(
            wrapper,
            text="Sistema Básico de Inventario",
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_AZUL,
            fg_color="white"
        ).pack(pady=(10, 4))

        ctk.CTkLabel(
            wrapper,
            text="Universidad de Sonora",
            font=("Segoe UI", 14),
            text_color="#374151",
            fg_color="white"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            wrapper,
            text=f"Bienvenido/a, {usuario} (rol: {rol})",
            font=("Segoe UI", 13),
            text_color="#444",
            fg_color="white"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            wrapper,
            text="Usa la barra superior para navegar entre Inicio, Productos, "
                 "Almacenes y Usuarios (solo ADMIN).",
            font=("Segoe UI", 11),
            text_color="#666",
            fg_color="white",
            wraplength=700,
            justify="center"
        ).pack(pady=(0, 20))


class App(ctk.CTk):
    """Ventana principal que controla login, navbar y vistas."""

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")
        self.title("Inventario - Universidad de Sonora")
        self.geometry("1080x650")
        self.minsize(960, 600)
        self.configure(fg_color=COLOR_FONDO)

        self.usuario = ""
        self.rol = ""

        self.navbar_frame = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        self.navbar_frame.pack(side="top", fill="x")

        self.container = ctk.CTkFrame(self, fg_color="white")
        self.container.pack(side="top", fill="both", expand=True)

        self.current_navbar = None

        self.show_login()

    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def clear_navbar(self):
        if self.current_navbar is not None:
            self.current_navbar.destroy()
            self.current_navbar = None

    def show_login(self):
        """Muestra la pantalla de Login (sin navbar)."""
        self.clear_navbar()
        self.clear_container()
        LoginView(self.container, on_ok=self.on_login).pack(fill="both", expand=True)

    def on_login(self, usuario, rol):
        """Callback cuando el login fue correcto."""
        self.usuario = usuario
        self.rol = (rol or "").upper()

        self.clear_navbar()
        self.current_navbar = NavBar(
            self.navbar_frame,
            rol=self.rol,
            on_home=self.show_home,
            on_prod=self.show_productos,
            on_alm=self.show_almacenes,
            on_users=self.show_usuarios,
            on_logout=self.logout,
        )
        self.current_navbar.pack(fill="x")

        self.show_home()

    def logout(self):
        """Cierra sesión y regresa al login."""
        if messagebox.askyesno("Cerrar sesión", "¿Seguro que quieres cerrar sesión?"):
            self.usuario = ""
            self.rol = ""
            self.show_login()

    def show_home(self):
        self.clear_container()
        HomeView(self.container, self.usuario, self.rol).pack(fill="both", expand=True)

    def show_productos(self):
        self.clear_container()
        ProductosView(self.container, self.usuario, self.rol).pack(fill="both", expand=True)

    def show_almacenes(self):
        self.clear_container()
        AlmacenesView(self.container, self.usuario, self.rol).pack(fill="both", expand=True)

    def show_usuarios(self):
        if self.rol != ROL_ADMIN:
            messagebox.showwarning("Permisos", "Solo el ADMIN puede acceder a Usuarios.")
            return
        self.clear_container()
        UsuariosView(self.container, self.usuario, self.rol).pack(fill="both", expand=True)


def main():
    # Asegurar que el esquema de la BD esté listo (tabla usuarios + auditoría)
    ensure_schema_and_seed_users()

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
