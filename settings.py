# ==========================================
# settings.py
# Configuración general de la aplicación
# ==========================================

# Nombre del archivo de base de datos SQLite
DB_FILE = "InventarioBD_2.db"

# Nombre del archivo de imagen del logo (debe estar en la misma carpeta que main.py)
LOGO_FILE = "escudo-unison-logo.png"

# Colores principales (paleta tipo UNISON)
COLOR_AZUL = "#00529e"
COLOR_AZUL_OSCURO = "#013159"
COLOR_DORADO = "#f8bb00"
COLOR_DORADO_OSCURO = "#d99900"

# Fuente principal de la interfaz
FONT_UI = ("Segoe UI", 11)

# Radio de esquina para botones
BTN_RADIUS = 8

# Roles del sistema
ROL_ADMIN = "ADMIN"
ROL_PROD = "PRODUCTOS"
ROL_ALM = "ALMACENES"
ROL_VISIT = "VISITANTE"  # Rol nuevo: solo lectura (ver/filtrar)
