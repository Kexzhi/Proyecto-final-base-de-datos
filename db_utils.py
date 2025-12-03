# ==========================================
# db_utils.py
# Manejo de base de datos:
# - conexión
# - esquema
# - usuarios (login y contraseñas)
# - auditoría de productos/almacenes
# ==========================================

import os
import sqlite3
import hashlib
import secrets
import re
from contextlib import contextmanager

from settings import DB_FILE, ROL_ADMIN, ROL_PROD, ROL_ALM, ROL_VISIT


# ------------------------------------------
# Ruta absoluta a la base de datos
# ------------------------------------------
def get_db_path() -> str:
    """
    Devuelve la ruta absoluta al archivo SQLite de la base de datos,
    usando como referencia la ubicación de este archivo.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_FILE)


DB_PATH = get_db_path()


# ------------------------------------------
# Context manager para conexión a DB
# ------------------------------------------
@contextmanager
def db():
    """
    Abre una conexión a SQLite con foreign_keys activado
    y la cierra automáticamente al final.
    Uso:
        with db() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
    finally:
        conn.close()


# ------------------------------------------
# Utilidades de esquema
# ------------------------------------------
def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Verifica si existe una tabla con el nombre dado."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)",
        (table,),
    )
    return cur.fetchone() is not None


def table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Verifica si una tabla tiene una columna específica."""
    try:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        return column in cols
    except Exception:
        return False


def ensure_column(conn: sqlite3.Connection, table: str, column: str, col_def: str,
                  set_default_sql: str | None = None):
    """
    Asegura que exista una columna en la tabla:
      - si no existe, la agrega
      - si se da set_default_sql, lo ejecuta para inicializar datos viejos
    """
    if not table_has_column(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        if set_default_sql:
            conn.execute(set_default_sql)


# ------------------------------------------
# Manejo de contraseñas (hash + salt)
# ------------------------------------------
def _pack_password_sha256(plain: str) -> str:
    """
    Recibe una contraseña en texto plano y devuelve un string:
        'sha256$salt$hash'
    con:
      - salt: valor aleatorio en hex
      - hash: SHA-256(salt + contraseña)
    """
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
    return f"sha256${salt}${h}"


def _unpack_password_sha256(packed: str):
    """
    Recibe 'sha256$salt$hash' y devuelve (salt, hash).
    Si no cumple el formato, devuelve None.
    """
    m = re.fullmatch(r"sha256\$([0-9a-fA-F]+)\$([0-9a-fA-F]{64})", packed or "")
    if not m:
        return None
    return m.group(1), m.group(2)


def verify_password(plain: str, packed: str) -> bool:
    """
    Verifica si la contraseña 'plain' coincide con el hash 'packed'
    almacenado en la base de datos.
    """
    parts = _unpack_password_sha256(packed)
    if not parts:
        return False
    salt, stored_hash = parts
    calc = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
    return secrets.compare_digest(calc, stored_hash)


# ------------------------------------------
# Esquema y usuarios base
# ------------------------------------------
def ensure_schema_and_seed_users():
    """
    Asegura:
      - que exista la tabla 'usuarios' con columnas: nombre, password,
        fecha_hora_ultimo_inicio, rol
      - que productos y almacenes tengan columnas de auditoría:
        fecha_hora_creacion, fecha_hora_ultima_modificacion, ultimo_usuario_en_modificar
      - que existan usuarios base:
        ADMIN, PRODUCTOS, ALMACENES, VISITANTE
    """
    with db() as conn:
        cur = conn.cursor()

        # 1) Crear tabla usuarios si no existe (sin CHECK rígido en rol)
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios(
                                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                           nombre TEXT UNIQUE,
                                                           password TEXT,
                                                           fecha_hora_ultimo_inicio TEXT,
                                                           rol TEXT
                    )
                    """)
        conn.commit()

        # 2) Asegurar columnas mínimas (por compatibilidad con esquemas viejos)
        for col in ("nombre", "password", "fecha_hora_ultimo_inicio", "rol"):
            if not table_has_column(conn, "usuarios", col):
                conn.execute(f"ALTER TABLE usuarios ADD COLUMN {col} TEXT")
        conn.commit()

        import sqlite3 as _sqlite3  # para IntegrityError

        # 3) Helper para insertar/actualizar usuarios de base
        def upsert_user(nombre: str, plain: str, rol: str):
            """
            Inserta o actualiza un usuario de base con contraseña cifrada.
            Si ya existe (por nombre exacto), actualiza password y rol.
            """
            packed = _pack_password_sha256(plain)
            row = conn.execute(
                "SELECT id FROM usuarios WHERE nombre=?",
                (nombre,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE usuarios SET password=?, rol=? WHERE id=?",
                    (packed, rol, row[0]),
                )
            else:
                try:
                    conn.execute(
                        "INSERT INTO usuarios(nombre, password, fecha_hora_ultimo_inicio, rol) "
                        "VALUES (?, ?, NULL, ?)",
                        (nombre, packed, rol),
                    )
                except _sqlite3.IntegrityError:
                    # Si hay constraints raros, evitamos que truene
                    pass

        # 4) Usuarios base
        upsert_user("ADMIN", "admin23", ROL_ADMIN)
        upsert_user("PRODUCTOS", "productos19", ROL_PROD)
        upsert_user("ALMACENES", "almacenes11", ROL_ALM)
        upsert_user("VISITANTE", "visitante1", ROL_VISIT)
        conn.commit()

        # 5) Auditoría en productos y almacenes
        for table in ("productos", "almacenes"):
            if table_exists(conn, table):
                # fecha_hora_creacion
                ensure_column(
                    conn, table, "fecha_hora_creacion",
                    "fecha_hora_creacion TEXT",
                    set_default_sql=(
                        f"UPDATE {table} SET fecha_hora_creacion="
                        f"COALESCE(fecha_hora_creacion, datetime('now'))"
                    )
                )
                # fecha_hora_ultima_modificacion
                ensure_column(
                    conn, table, "fecha_hora_ultima_modificacion",
                    "fecha_hora_ultima_modificacion TEXT"
                )
                # ultimo_usuario_en_modificar
                ensure_column(
                    conn, table, "ultimo_usuario_en_modificar",
                    "ultimo_usuario_en_modificar TEXT"
                )
        conn.commit()


# ------------------------------------------
# Autenticación (login)
# ------------------------------------------
def authenticate(nombre: str, password: str):
    """
    Verifica usuario y contraseña.
    IMPORTANTE:
      - El nombre de usuario es SENSIBLE a mayúsculas/minúsculas.
        Es decir, si en la BD está 'ADMIN', escribir 'admin' NO funciona.
    Devuelve (id, nombre, rol) si es válido, o None si no.
    """
    with db() as conn:
        conn.row_factory = sqlite3.Row

        # Aquí comparamos nombre EXACTO (sin UPPER)
        row = conn.execute(
            "SELECT id, nombre, password, rol FROM usuarios WHERE nombre=?",
            (nombre,),
        ).fetchone()

        if not row:
            return None

        if not verify_password(password, row["password"] or ""):
            return None

        # Actualizamos la fecha/hora del último inicio de sesión
        conn.execute(
            "UPDATE usuarios SET fecha_hora_ultimo_inicio=datetime('now') WHERE id=?",
            (row["id"],)
        )
        conn.commit()

        # Normalizamos rol en mayúsculas para el resto de la app
        return row["id"], row["nombre"], (row["rol"] or "").upper().strip()


# ------------------------------------------
# Auditoría para productos/almacenes
# ------------------------------------------
def touch_audit(conn: sqlite3.Connection, table: str, usuario: str, row_id: int):
    """
    Actualiza columnas de auditoría en un registro:
      - fecha_hora_ultima_modificacion
      - ultimo_usuario_en_modificar
    """
    conn.execute(
        f"UPDATE {table} SET "
        f"fecha_hora_ultima_modificacion = datetime('now'), "
        f"ultimo_usuario_en_modificar   = ? "
        f"WHERE id = ?",
        (usuario, row_id),
    )
