"""Database layer for El Perro Wero — SQLite with raw sqlite3."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

DB_PATH = "el_perro_wero.db"

# ---------------------------------------------------------------------------
# DDL constants
# ---------------------------------------------------------------------------

DDL_PRODUCTOS = """
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    categoria TEXT NOT NULL CHECK (categoria IN ('jocho', 'hamburguesa')),
    imagen_url TEXT,
    disponible INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0, 1))
);
"""

DDL_CLIENTES = """
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT NOT NULL UNIQUE,
    edad INTEGER NOT NULL,
    genero TEXT NOT NULL CHECK (genero IN ('M', 'F', 'Otro'))
);
"""

DDL_ORDENES = """
CREATE TABLE IF NOT EXISTS ordenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_orden TEXT NOT NULL,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    sku TEXT NOT NULL,
    producto TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_CONFIGURACION = """
CREATE TABLE IF NOT EXISTS configuracion (
    llave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED_PRODUCTOS = [
    ("JO-001", "Jocho Clásico",        "Salchicha, jitomate, cebolla, mostaza, catsup", 65.0,  "jocho",        None, 1),
    ("JO-002", "Jocho Hawaiano",        "Salchicha, piña, jamón, queso",                  75.0,  "jocho",        None, 1),
    ("JO-003", "Jocho Italiano",        "Pepperoni, queso costra, orégano",               85.0,  "jocho",        None, 1),
    ("HB-001", "Hamburguesa Sencilla",  "Carne, queso, lechuga, jitomate",               90.0,  "hamburguesa",  None, 1),
    ("HB-002", "Hamburguesa con Tocino","Carne, queso, tocino, lechuga",                110.0,  "hamburguesa",  None, 1),
    ("HB-003", "Hamburguesa BBQ",       "Carne, queso, aros de cebolla, BBQ",           120.0,  "hamburguesa",  None, 1),
]

SEED_CLIENTES = [
    ("Juan Pérez",  "5551234567", 28, "M"),
    ("María López", "5559876543", 35, "F"),
]

SEED_CONFIG: dict[str, str] = {
    "banner_promocion": "¡SÚPER PROMO! 2 Hamburguesas con Tocino + Papas por $200",
    "horarios_texto":   "Jueves a Domingo · 19:00 — 02:00 hrs",
    "ubicacion_texto":  "Paseos del Pedregal · Envío a domicilio GRATIS por la zona",
    "whatsapp_numero":  "4421231234",  # TODO: replace with the real business number
    "facebook_url":     "https://facebook.com/jochoselperrowero",
    "didi_food_url":    "https://didifood.com/jochos",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a sqlite3 connection with Row factory and FK enforcement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create all 4 tables and seed data idempotently."""
    with get_db() as conn:
        conn.executescript(
            DDL_PRODUCTOS + DDL_CLIENTES + DDL_ORDENES + DDL_CONFIGURACION
        )
        cur = conn.cursor()

        # productos: seed only if table is empty
        if cur.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO productos (sku, nombre, descripcion, precio, categoria, imagen_url, disponible) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                SEED_PRODUCTOS,
            )

        # clientes: seed only if table is empty
        if cur.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO clientes (nombre, telefono, edad, genero) VALUES (?, ?, ?, ?)",
                SEED_CLIENTES,
            )

        # configuracion: idempotent via INSERT OR IGNORE (llave is PK)
        cur.executemany(
            "INSERT OR IGNORE INTO configuracion (llave, valor) VALUES (?, ?)",
            list(SEED_CONFIG.items()),
        )

        conn.commit()