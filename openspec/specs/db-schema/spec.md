# Capability: db-schema

## Purpose
SQLite database with 4 tables (clientes, ordenes, configuracion, productos) and an idempotent `init_db()` that seeds Mexican-Spanish content for the "Jochos El Perro Wero" menu and site config.

> **Note**: the original change-001-foundation proposal mentioned 3 tables, but during design we added a `productos` table (with a `disponible` toggle column) because product data is structured and needs admin-controlled Sold Out state, which does not fit the `configuracion` key/value shape.

> **Spec home**: This file is the canonical home of the `db-schema` capability. Originally a duplicate existed in `change-001-foundation/specs/db-schema/` for review-time proximity during the stacked-to-main PR cycle; both have been archived together as `2026-06-07-change-001-foundation` and `2026-06-07-change-002-db-seed`.

## Requirements

### Requirement: clientes table
The system MUST create a `clientes` table with columns:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `nombre` TEXT NOT NULL
- `telefono` TEXT NOT NULL
- `edad` INTEGER NOT NULL
- `genero` TEXT NOT NULL CHECK (genero IN ('M', 'F', 'Otro'))

### Requirement: ordenes table
The system MUST create a `ordenes` table with columns:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `numero_orden` TEXT NOT NULL
- `cliente_id` INTEGER NOT NULL REFERENCES clientes(id)
- `sku` TEXT NOT NULL
- `producto` TEXT NOT NULL
- `precio` REAL NOT NULL CHECK (precio >= 0)
- `cantidad` INTEGER NOT NULL CHECK (cantidad > 0)
- `fecha_hora` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

### Requirement: configuracion table
The system MUST create a `configuracion` table with columns:
- `llave` TEXT PRIMARY KEY
- `valor` TEXT NOT NULL

### Requirement: productos table
The system MUST create a `productos` table with columns:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `sku` TEXT NOT NULL UNIQUE
- `nombre` TEXT NOT NULL
- `descripcion` TEXT NOT NULL
- `precio` REAL NOT NULL CHECK (precio >= 0)
- `categoria` TEXT NOT NULL CHECK (categoria IN ('jocho', 'hamburguesa'))
- `imagen_url` TEXT
- `disponible` INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0, 1))

### Requirement: init_db function
The system MUST expose `init_db()` in `app/db.py` that:
- Creates all 4 tables if they do not exist (idempotent)
- Inserts seed data ONLY if the relevant table is empty (idempotent — uses `SELECT COUNT(*)` guard)
- Returns `None` on success
- Raises on unrecoverable I/O or SQL error

### Requirement: seed productos
The system MUST seed exactly these 6 products (all `disponible=1`):
- `JO-001` Jocho Clásico — Salchicha, jitomate, cebolla, mostaza, catsup — $65 — jocho
- `JO-002` Jocho Hawaiano — Salchicha, piña, jamón, queso — $75 — jocho
- `JO-003` Jocho Italiano — Pepperoni, queso costra, orégano — $85 — jocho
- `HB-001` Hamburguesa Sencilla — Carne, queso, lechuga, jitomate — $90 — hamburguesa
- `HB-002` Hamburguesa con Tocino — Carne, queso, tocino, lechuga — $110 — hamburguesa
- `HB-003` Hamburguesa BBQ — Carne, queso, aros de cebolla, BBQ — $120 — hamburguesa

### Requirement: seed clientes
The system MUST seed exactly these 2 sample clients:
- "Juan Pérez" (tel: 5551234567, edad: 28, genero: M)
- "María López" (tel: 5559876543, edad: 35, genero: F)

### Requirement: seed configuracion
The system MUST seed these exact config keys/values:
- `banner_promocion` = "¡SÚPER PROMO! 2 Hamburguesas con Tocino + Papas por $200"
- `horarios_texto` = "Jueves a Domingo · 19:00 — 02:00 hrs"
- `ubicacion_texto` = "Paseos del Pedregal · Envío a domicilio GRATIS por la zona"
- `whatsapp_numero` = "525555555555"
- `facebook_url` = "https://facebook.com/jochoselperrowero"
- `didi_food_url` = "https://didifood.com/jochos"

### Requirement: database file location
The system MUST create the SQLite file at the project root as `el_perro_wero.db` (gitignored).

### Requirement: get_db context manager
The system MUST expose `get_db()` in `app/db.py` as a context manager that:
- Yields a `sqlite3.Connection` with `row_factory=sqlite3.Row`
- Sets `PRAGMA foreign_keys = ON` on connect
- Closes the connection on context exit
- Does not commit automatically (caller commits)

#### Scenario: fresh init creates all tables
- **GIVEN** the database file `el_perro_wero.db` does not exist
- **WHEN** `init_db()` is called
- **THEN** the file is created and all 4 tables (clientes, ordenes, configuracion, productos) exist in the SQLite schema

#### Scenario: init is idempotent
- **GIVEN** `init_db()` has been called once
- **WHEN** `init_db()` is called a second time
- **THEN** the `productos` row count remains exactly 6, the `clientes` row count remains exactly 2, and the `configuracion` row count remains exactly 6

#### Scenario: seed includes both categories
- **GIVEN** `init_db()` has run on an empty database
- **WHEN** the productos table is queried with `SELECT categoria, COUNT(*) FROM productos GROUP BY categoria`
- **THEN** there are at least 2 rows with `categoria='jocho'` and at least 2 rows with `categoria='hamburguesa'`

#### Scenario: all config keys present
- **GIVEN** `init_db()` has run on an empty database
- **WHEN** `SELECT llave FROM configuracion` is executed
- **THEN** the 6 required keys are all present: `banner_promocion`, `horarios_texto`, `ubicacion_texto`, `whatsapp_numero`, `facebook_url`, `didi_food_url`

#### Scenario: foreign keys are enforced
- **GIVEN** a connection returned by `get_db()`
- **WHEN** `PRAGMA foreign_keys` is queried
- **THEN** the result is `1`

