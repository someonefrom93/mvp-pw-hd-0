# Design: Change 002 — DB Seed

## 1. Overview

Focused design for the database layer. The `app/db.py` module is the only place where SQL strings live; everything else (route handlers, templates, models) consumes typed dataclasses from `app/models.py`. The 4-table schema is normalized for a local MVP: customers, orders, config (key/value), and products with a `disponible` toggle.

## 2. File Tree (this change only)

```
app/
├── db.py          (NEW, ~120 LOC)
└── models.py      (NEW, ~60 LOC)

app/main.py        (1 line modified — lifespan body)
```

No other files change in this change.

## 3. Module Responsibilities

| File | Responsibility | Public symbols |
|------|----------------|----------------|
| `app/db.py` | Connection management, DDL constants, seed data, idempotent `init_db()` | `DB_PATH`, `DDL_*` (4 constants), `SEED_PRODUCTOS`, `SEED_CLIENTES`, `SEED_CONFIG`, `get_db()`, `init_db()` |
| `app/models.py` | Typed read-side wrappers for `sqlite3.Row` | `Producto`, `Cliente`, `ConfigKey`, `OrdenLine` — each with `from_row()` classmethod |
| `app/main.py` (lifespan edit) | Call `init_db()` on startup | (no new public symbol; one new line) |

## 4. Database Layer Design

### 4.1 Connection management

`get_db()` is a `@contextmanager` that:
1. Opens `sqlite3.connect(DB_PATH)` with default isolation level
2. Sets `row_factory = sqlite3.Row` so rows are dict-like
3. Executes `PRAGMA foreign_keys = ON`
4. Yields the connection
5. Closes on context exit (no auto-commit; caller commits)

```python
from contextlib import contextmanager
import sqlite3

DB_PATH = "el_perro_wero.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
```

### 4.2 DDL constants

Four `DDL_*` string constants — one per table. SQLite-compatible, executed via `executescript` for table creation.

```python
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
    telefono TEXT NOT NULL,
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
```

### 4.3 Seed data

Three lists of tuples / dicts. `init_db()` uses `INSERT OR IGNORE` for config (key is the PK) and a `SELECT COUNT(*) == 0` guard for the others.

```python
SEED_PRODUCTOS = [
    ("JO-001", "Jocho Clásico",       "Salchicha, jitomate, cebolla, mostaza, catsup", 65.0,  "jocho",       None, 1),
    ("JO-002", "Jocho Hawaiano",       "Salchicha, piña, jamón, queso",                 75.0,  "jocho",       None, 1),
    ("JO-003", "Jocho Italiano",       "Pepperoni, queso costra, orégano",               85.0,  "jocho",       None, 1),
    ("HB-001", "Hamburguesa Sencilla", "Carne, queso, lechuga, jitomate",               90.0,  "hamburguesa", None, 1),
    ("HB-002", "Hamburguesa con Tocino","Carne, queso, tocino, lechuga",                110.0, "hamburguesa", None, 1),
    ("HB-003", "Hamburguesa BBQ",      "Carne, queso, aros de cebolla, BBQ",            120.0, "hamburguesa", None, 1),
]

SEED_CLIENTES = [
    ("Juan Pérez",  "5551234567", 28, "M"),
    ("María López", "5559876543", 35, "F"),
]

SEED_CONFIG = {
    "banner_promocion": "¡SÚPER PROMO! 2 Hamburguesas con Tocino + Papas por $200",
    "horarios_texto":   "Jueves a Domingo · 19:00 — 02:00 hrs",
    "ubicacion_texto":  "Paseos del Pedregal · Envío a domicilio GRATIS por la zona",
    "whatsapp_numero":  "525555555555",
    "facebook_url":     "https://facebook.com/jochoselperrowero",
    "didi_food_url":    "https://didifood.com/jochos",
}
```

### 4.4 init_db() — idempotent

```python
def init_db() -> None:
    with get_db() as conn:
        conn.executescript(DDL_PRODUCTOS + DDL_CLIENTES + DDL_ORDENES + DDL_CONFIGURACION)

        cur = conn.cursor()

        # Productos: only seed if empty
        if cur.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO productos (sku, nombre, descripcion, precio, categoria, imagen_url, disponible) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                SEED_PRODUCTOS,
            )

        # Clientes: only seed if empty
        if cur.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO clientes (nombre, telefono, edad, genero) VALUES (?, ?, ?, ?)",
                SEED_CLIENTES,
            )

        # Configuracion: idempotent via INSERT OR IGNORE (llave is PK)
        cur.executemany(
            "INSERT OR IGNORE INTO configuracion (llave, valor) VALUES (?, ?)",
            list(SEED_CONFIG.items()),
        )

        conn.commit()
```

## 5. Models.py Type Contracts

Four `@dataclass(slots=True, frozen=True)` classes. `from_row()` classmethod maps `sqlite3.Row` → typed Python.

```python
from dataclasses import dataclass
from typing import Literal
import sqlite3

@dataclass(slots=True, frozen=True)
class Producto:
    id: int
    sku: str
    nombre: str
    descripcion: str
    precio: float
    categoria: Literal["jocho", "hamburguesa"]
    imagen_url: str | None
    disponible: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Producto":
        return cls(
            id=row["id"],
            sku=row["sku"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            precio=row["precio"],
            categoria=row["categoria"],
            imagen_url=row["imagen_url"],
            disponible=bool(row["disponible"]),
        )

@dataclass(slots=True, frozen=True)
class Cliente:
    id: int
    nombre: str
    telefono: str
    edad: int
    genero: Literal["M", "F", "Otro"]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Cliente":
        return cls(id=row["id"], nombre=row["nombre"], telefono=row["telefono"],
                   edad=row["edad"], genero=row["genero"])

@dataclass(slots=True, frozen=True)
class ConfigKey:
    llave: str
    valor: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ConfigKey":
        return cls(llave=row["llave"], valor=row["valor"])

@dataclass(slots=True, frozen=True)
class OrdenLine:
    id: int
    numero_orden: str
    cliente_id: int
    sku: str
    producto: str
    precio: float
    cantidad: int
    fecha_hora: str  # ISO 8601 string from SQLite

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "OrdenLine":
        return cls(
            id=row["id"],
            numero_orden=row["numero_orden"],
            cliente_id=row["cliente_id"],
            sku=row["sku"],
            producto=row["producto"],
            precio=row["precio"],
            cantidad=row["cantidad"],
            fecha_hora=row["fecha_hora"],
        )
```

## 6. Lifespan Wire-up (the 1-line change in `app/main.py`)

`change-001-foundation` writes `app/main.py` with a lifespan body that calls `init_db()`. This change does NOT touch `app/main.py` directly — the lifespan call is already in place. **However**, after `change-001-foundation` lands, the import `from app.db import init_db` will resolve. **No edit to `app/main.py` is needed in this change.** The companion change handles the wire-up.

> Cross-check: the original `app-skeleton` spec requirement "call init_db() on startup" is implemented in `change-001-foundation`'s T3. The DB layer that satisfies the symbol is in this change's T2. Stacked-to-main PR order ensures both are present on `main` once both PRs merge.

## 7. Key Decisions and Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | None — raw `sqlite3` | MVP transparency; fewer deps |
| `disponible` storage | INTEGER 0/1, mapped to `bool` in Python | SQLite has no native bool; standard pattern |
| Seed idempotency | `SELECT COUNT(*) == 0` for productos/clientes, `INSERT OR IGNORE` for configuracion | Config keys are unique by PK; bulk rows are guarded by count |
| DDL execution | `executescript` (single transaction) | Atomic table creation; clean error semantics |
| Dataclass slots | `slots=True` | Memory + attribute access perf |
| Dataclass frozen | `frozen=True` | Immutability for read-side wrappers; safer to share across threads |
| `fecha_hora` type | `str` in Python dataclass | SQLite returns TIMESTAMP as ISO string; route handlers format it for display |
| `imagen_url` nullable | `str | None` | Seed has `None`; will be filled in change-002-features |
| Connection closing | `try/finally` in context manager | Guarantees close even on exception |
| `PRAGMA foreign_keys` | Set on every connect | SQLite defaults to OFF per connection; must re-enable |
| No migrations framework | `CREATE TABLE IF NOT EXISTS` only | MVP; schema changes are greenfield-only |

## 8. Out of Scope (deferred)

- Pydantic request/response models (change-002-features needs them for forms)
- Order insertion logic (change-002-features writes the `POST /orden` route)
- Admin `disponible` toggle writes (change-002-features admin panel)
- Real product images (change-002-features)

## 9. Risks

- **Cross-PR lifespan import**: `app/main.py` in change-001-foundation imports `from app.db import init_db` which doesn't exist until this change lands on main. **Mitigation**: stacked-to-main PR order — this change (change-002) merges FIRST, so the import resolves before change-001's CI runs.
- **No type safety on raw SQL**: a typo in column name won't be caught until runtime. **Mitigation**: mypy on the dataclass layer; integration smoke test runs after every merge.
- **Single connection at a time**: `get_db()` opens/closes per call — no pooling. **Mitigation**: fine for local MVP single-user.
- **Seed data drift**: if menu changes (new product), seed is not re-applied. **Mitigation**: change-002-features admin panel uses DB writes, not seed replay.
