# db_utils.py
"""
Utilidades de base de datos para el sistema de inventario UNISON.

- Maneja la conexión a SQLite.
- Asegura el esquema de la BD (tabla usuarios + columnas de auditoría).
- Autenticación de usuarios (case sensitive, respeta mayúsculas/minúsculas).
- Operaciones CRUD básicas para usuarios y almacenes.
"""

import sqlite3
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime

from settings import DB_FILE, ROL_ADMIN, ROL_PROD, ROL_ALM, ROL_VIS


# ---------- Conexión básica ----------

@contextmanager
def db():
    """Context manager para abrir/usar/cerrar la conexión."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Devuelve True si existe la tabla dada."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None


def table_has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    """Devuelve True si la tabla tiene la columna dada."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row["name"] == col for row in cur.fetchall())


# ---------- Hash de contraseñas ----------

def _hash_password(plain: str, salt: str | None = None) -> tuple[str, str]:
    """Devuelve (salt, hash) usando SHA-256."""
    if salt is None:
        salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
    return salt, h


def _verify_password(plain: str, salt: str, stored_hash: str) -> bool:
    """Verifica una contraseña en texto plano contra (salt, hash) almacenados."""
    _, h = _hash_password(plain, salt)
    return h == stored_hash


# ---------- Esquema y datos base ----------

def ensure_schema_and_seed_users() -> None:
    """
    Asegura que exista la tabla usuarios con las columnas correctas y
    crea/actualiza los usuarios base (respetando mayúsculas):

      - ADMIN     / admin23      / ADMIN
      - PRODUCTOS / productos19  / PRODUCTOS
      - ALMACENES / almacenes11  / ALMACENES
      - VISITANTE / visitante00  / VISITANTE
    """
    with db() as conn:
        # 1) Crear tabla usuarios si no existe
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    nombre TEXT UNIQUE,
                                                    password_hash TEXT,
                                                    salt TEXT,
                                                    fecha_hora_ultimo_inicio TEXT,
                                                    rol TEXT CHECK(rol IN ('ADMIN','PRODUCTOS','ALMACENES','VISITANTE'))
                )
            """
        )

        # 2) Asegurar columnas por si la tabla viene de otra versión
        if not table_has_column(conn, "usuarios", "salt"):
            conn.execute("ALTER TABLE usuarios ADD COLUMN salt TEXT")
        if not table_has_column(conn, "usuarios", "password_hash"):
            conn.execute("ALTER TABLE usuarios ADD COLUMN password_hash TEXT")
        if not table_has_column(conn, "usuarios", "fecha_hora_ultimo_inicio"):
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN fecha_hora_ultimo_inicio TEXT"
            )
        if not table_has_column(conn, "usuarios", "rol"):
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN rol TEXT "
                "CHECK(rol IN ('ADMIN','PRODUCTOS','ALMACENES','VISITANTE'))"
            )

        # 3) Upsert de usuarios base (respetando mayúsculas)
        def upsert_user(nombre: str, plain_pw: str, rol: str) -> None:
            salt, h = _hash_password(plain_pw)
            cur = conn.execute(
                "SELECT id FROM usuarios WHERE nombre=?",
                (nombre,),
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE usuarios SET password_hash=?, salt=?, rol=? "
                    "WHERE id=?",
                    (h, salt, rol, row["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO usuarios(nombre, password_hash, salt, "
                    "fecha_hora_ultimo_inicio, rol) "
                    "VALUES (?,?,?,NULL,?)",
                    (nombre, h, salt, rol),
                )

        upsert_user("ADMIN", "admin23", ROL_ADMIN)
        upsert_user("PRODUCTOS", "productos19", ROL_PROD)
        upsert_user("ALMACENES", "almacenes11", ROL_ALM)
        upsert_user("VISITANTE", "visitante00", ROL_VIS)


# ---------- Autenticación (estricta con mayúsculas) ----------

def authenticate(nombre: str, plain_pw: str) -> tuple[str, str] | None:
    """
    Autentica un usuario.

    IMPORTANTE: es **sensible** a mayúsculas/minúsculas.
    Si en la BD está 'ADMIN', solo 'ADMIN' funciona. 'admin' falla.

    Devuelve (nombre, rol) si es válido o None si falla.
    """
    nombre = nombre.strip()
    if not nombre or not plain_pw:
        return None

    with db() as conn:
        cur = conn.execute(
            "SELECT id, nombre, password_hash, salt, rol "
            "FROM usuarios WHERE nombre = ?",  # SIN UPPER()
            (nombre,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        if not _verify_password(plain_pw, row["salt"], row["password_hash"]):
            return None

        # Actualizar último inicio de sesión
        conn.execute(
            "UPDATE usuarios SET fecha_hora_ultimo_inicio=? WHERE id=?",
            (datetime.now().isoformat(sep=" ", timespec="seconds"), row["id"]),
        )

        return row["nombre"], row["rol"]


def authenticate_user(nombre: str, plain_pw: str) -> tuple[bool, str, str, str]:
    """
    Wrapper para compatibilidad con views_login.

    Devuelve:
        (ok, nombre, rol, msg)

        ok   -> True si el login fue exitoso, False si falló.
        nombre, rol -> datos del usuario si ok == True, o "" si falló.
        msg  -> mensaje de error para mostrar en la UI si ok == False.
    """
    # Llamamos a la función base
    result = authenticate(nombre, plain_pw)

    if result is None:
        # Falló autenticación
        return False, "", "", "Usuario o contraseña incorrectos.\nRevisa mayúsculas y minúsculas."

    nombre_db, rol = result
    return True, nombre_db, rol, ""


# ---------- Auditoría genérica ----------

def touch_audit(
        conn: sqlite3.Connection,
        table: str,
        row_id: int,
        usuario: str,
) -> None:
    """
    Actualiza columnas de auditoría si existen en la tabla:
      - fecha_hora_ultima_modificacion
      - ultimo_usuario_en_modificar
    """
    if table_has_column(conn, table, "fecha_hora_ultima_modificacion"):
        conn.execute(
            f"UPDATE {table} SET fecha_hora_ultima_modificacion=? WHERE id=?",
            (datetime.now().isoformat(sep=" ", timespec="seconds"), row_id),
        )
    if table_has_column(conn, table, "ultimo_usuario_en_modificar"):
        conn.execute(
            f"UPDATE {table} SET ultimo_usuario_en_modificar=? WHERE id=?",
            (usuario, row_id),
        )


# ---------- Usuarios (CRUD básico) ----------

def list_users() -> list[sqlite3.Row]:
    """Devuelve todos los usuarios."""
    with db() as conn:
        cur = conn.execute(
            "SELECT id, nombre, rol, fecha_hora_ultimo_inicio "
            "FROM usuarios ORDER BY id"
        )
        return cur.fetchall()


def create_user(nombre: str, plain_pw: str, rol: str) -> None:
    """Crea un usuario nuevo."""
    salt, h = _hash_password(plain_pw)
    with db() as conn:
        conn.execute(
            "INSERT INTO usuarios(nombre, password_hash, salt, "
            "fecha_hora_ultimo_inicio, rol) "
            "VALUES (?,?,?,NULL,?)",
            (nombre.strip(), h, salt, rol),
        )


def update_user(user_id: int, nombre: str, plain_pw: str | None, rol: str) -> None:
    """Actualiza datos de un usuario (con o sin cambio de contraseña)."""
    with db() as conn:
        if plain_pw:
            salt, h = _hash_password(plain_pw)
            conn.execute(
                "UPDATE usuarios SET nombre=?, password_hash=?, salt=?, rol=? "
                "WHERE id=?",
                (nombre.strip(), h, salt, rol, user_id),
            )
        else:
            conn.execute(
                "UPDATE usuarios SET nombre=?, rol=? WHERE id=?",
                (nombre.strip(), rol, user_id),
            )


def delete_user(user_id: int) -> None:
    """Elimina un usuario por id."""
    with db() as conn:
        conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))


# ---------- Almacenes (CRUD básico) ----------

def list_almacenes(
        nombre_like: str | None = None,
) -> list[sqlite3.Row]:
    """
    Lista almacenes con filtro opcional por nombre (LIKE).
    """
    sql = (
        "SELECT id, nombre, fecha_hora_creacion, "
        "fecha_hora_ultima_modificacion, ultimo_usuario_en_modificar "
        "FROM almacenes WHERE 1=1"
    )
    params: list[object] = []
    if nombre_like:
        sql += " AND nombre LIKE ?"
        params.append(f"%{nombre_like}%")
    sql += " ORDER BY id"

    with db() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()


def create_almacen(nombre: str, usuario: str) -> None:
    """Crea un almacén y registra auditoría."""
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO almacenes("
            "nombre, fecha_hora_creacion, fecha_hora_ultima_modificacion, "
            "ultimo_usuario_en_modificar"
            ") VALUES (?,?,?,?)",
            (nombre.strip(), now, now, usuario),
        )
        almacen_id = cur.lastrowid
        touch_audit(conn, "almacenes", almacen_id, usuario)


def update_almacen(almacen_id: int, nombre: str, usuario: str) -> None:
    """Actualiza el nombre de un almacén y su auditoría."""
    with db() as conn:
        conn.execute(
            "UPDATE almacenes SET nombre=? WHERE id=?",
            (nombre.strip(), almacen_id),
        )
        touch_audit(conn, "almacenes", almacen_id, usuario)


def delete_almacen(almacen_id: int) -> None:
    """Elimina un almacén por id."""
    with db() as conn:
        conn.execute("DELETE FROM almacenes WHERE id=?", (almacen_id,))
