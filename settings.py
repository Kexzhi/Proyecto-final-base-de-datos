# settings.py
# -----------------------------------------
# Ajustes generales de la aplicación:
# - ruta de la base de datos
# - colores y fuente
# - constantes de roles
# -----------------------------------------

# Nombre del archivo de la base de datos SQLite
DB_FILE = "InventarioBD_2.db"

# Fuente base para la interfaz
FONT_UI = ("Segoe UI", 11)

# Colores institucionales UNISON
COLOR_AZUL = "#00529e"
COLOR_DORADO = "#f8bb00"
COLOR_DORADO_OSCURO = "#d9a300"

# Colores de fondo y texto
COLOR_FONDO = "#f3f4f6"
COLOR_TEXTO = "#111827"

# Fondo de paneles
COLOR_PANEL = "#ffffff"

# Radio de los bordes de los botones
BTN_RADIUS = 10

# Archivo de logo (debe estar junto a los .py o el .exe)
LOGO_FILE = "escudo-unison-logo.png"

# Constantes de rol de usuario
ROL_ADMIN = "ADMIN"       # Administrador
ROL_PROD  = "PRODUCTOS"   # Módulo productos
ROL_ALM   = "ALMACENES"   # Módulo almacenes
ROL_VIS   = "VISITANTE"   # 👈 NUEVO rol de solo vista