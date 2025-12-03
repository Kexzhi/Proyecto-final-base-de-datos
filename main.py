# ==========================================
# main.py
# Punto de entrada de la aplicación:
# - configura la ventana
# - muestra login, luego home y vistas
# ==========================================

import customtkinter as ctk
from tkinter import messagebox

from settings import COLOR_AZUL, ROL_ADMIN
from db_utils import ensure_schema_and_seed_users
from ui_widgets import NavBar, load_logo
from views_login import LoginView
from views_productos import ProductosView
from views_almacenes import AlmacenesView
from views_usuarios import UsuariosView


class HomeView(ctk.CTkFrame):
    """Vista de inicio (bienvenida) después del login."""

    def __init__(self, parent, usuario: str, rol: str):
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
            text=f"Bienvenido/a, {usuario} (rol: {rol})",
            font=("Segoe UI", 13),
            text_color="#444", fg_color="white"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            wrapper,
            text="Usa la barra superior para navegar entre Inicio, Productos, Almacenes "
                 "y Usuarios (solo si eres ADMIN).",
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

        self.usuario = ""
        self.rol = ""

        self.navbar_frame = ctk.CTkFrame(self, fg_color=COLOR_AZUL)
        self.navbar_frame.pack(side="top", fill="x")

        self.container = ctk.CTkFrame(self, fg_color="white")
        self.container.pack(side="top", fill="both", expand=True)

        self.current_navbar = None

        # Al iniciar, vamos a login
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

    def on_login(self, usuario: str, rol: str):
        """Callback cuando el login es correcto."""
        self.usuario = usuario
        self.rol = (rol or "").upper()

        # Creamos navbar
        self.clear_navbar()
        self.current_navbar = NavBar(
            self.navbar_frame,
            on_home=self.show_home,
            on_prod=self.show_productos,
            on_alm=self.show_almacenes,
            on_users=self.show_usuarios,
            on_logout=self.logout,
            rol=self.rol
        )
        self.current_navbar.pack(fill="x")

        # Mostramos home
        self.show_home()

    def show_home(self):
        self.clear_container()
        HomeView(self.container, usuario=self.usuario, rol=self.rol).pack(fill="both", expand=True)

    def show_productos(self):
        self.clear_container()
        ProductosView(self.container, usuario=self.usuario, rol=self.rol).pack(fill="both", expand=True)

    def show_almacenes(self):
        self.clear_container()
        AlmacenesView(self.container, usuario=self.usuario, rol=self.rol).pack(fill="both", expand=True)

    def show_usuarios(self):
        if self.rol != ROL_ADMIN:
            messagebox.showwarning("Acceso", "Solo ADMIN puede gestionar usuarios.")
            return
        self.clear_container()
        UsuariosView(self.container).pack(fill="both", expand=True)

    def logout(self):
        """Cerrar sesión y volver a login."""
        self.usuario = ""
        self.rol = ""
        self.show_login()


def main():
    """Punto de entrada del programa."""
    ensure_schema_and_seed_users()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
