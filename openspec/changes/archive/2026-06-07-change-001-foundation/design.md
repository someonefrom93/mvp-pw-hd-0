# Design: Change 001 — Foundation

## 1. Overview

Greenfield FastAPI app for *Jochos El Perro Wero*. Single process serves public client UI, hidden admin UI, and `GET /healthz`. SQLite (`el_perro_wero.db`, gitignored) initializes on startup via lifespan. CSS splits into pure tokens (`tokens.css`) and a consumer file (`main.css`). No ORM, no Pydantic, no auth — everything else is change-002.

## 2. File Tree

```
el-perro-wero-hotdogsAndBurgers-1/
├── pyproject.toml
├── .gitignore                  (+el_perro_wero.db)
├── el_perro_wero.db            (gitignored, runtime)
├── README.md
└── app/
    ├── __init__.py
    ├── main.py
    ├── db.py
    ├── models.py
    ├── routes/
    │   ├── __init__.py
    │   ├── public.py           (APIRouter + GET /healthz)
    │   └── admin.py            (APIRouter, /admin prefix)
    ├── templates/
    │   ├── base.html
    │   └── base_admin.html
    └── static/
        ├── css/{tokens.css, main.css}
        ├── js/.gitkeep
        └── img/.gitkeep
```

## 3. Module Responsibilities

| File | Responsibility | Public symbols |
|------|----------------|----------------|
| `app/main.py` | App factory, lifespan, static mount, Jinja2, router registration | `app` |
| `app/db.py` | Connection, DDL, idempotent seed | `get_db()`, `init_db()`, `DB_PATH`, `DDL_*`, `SEED_*` |
| `app/models.py` | Read-side typed wrappers for `sqlite3.Row` | `Producto`, `Cliente`, `ConfigKey`, `OrdenLine` w/ `from_row` |
| `app/routes/public.py` | Root router; `GET /healthz` only this change | `router` |
| `app/routes/admin.py` | `/admin` placeholder, change-002 fills it | `router` |
| `templates/base.html` | Public HTML5 shell, fonts, CSS, `content`/`footer`/`extra_*` | — |
| `templates/base_admin.html` | Extends `base.html`; topbar + `admin_content`/`admin_scripts` | — |
| `static/css/tokens.css` | `:root` design tokens only | — |
| `static/css/main.css` | Reset + base typography | — |

## 4. Database Layer Design

`get_db()` is a `@contextmanager`: opens `sqlite3.connect(DB_PATH)`, sets `row_factory = sqlite3.Row`, runs `PRAGMA foreign_keys = ON`, yields, closes. No auto-commit. Raw SQL + typed wrappers = no ORM dep, full SQL visibility, mypy-checkable shapes.

```python
DDL_CLIENTES  = "CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, telefono TEXT NOT NULL, edad INTEGER NOT NULL, genero TEXT NOT NULL CHECK (genero IN ('M','F','Otro')))"
DDL_ORDENES   = "CREATE TABLE IF NOT EXISTS ordenes (id INTEGER PRIMARY KEY AUTOINCREMENT, numero_orden TEXT NOT NULL, cliente_id INTEGER NOT NULL REFERENCES clientes(id), sku TEXT NOT NULL, producto TEXT NOT NULL, precio REAL NOT NULL CHECK (precio >= 0), cantidad INTEGER NOT NULL CHECK (cantidad > 0), fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
DDL_CONFIG    = "CREATE TABLE IF NOT EXISTS configuracion (llave TEXT PRIMARY KEY, valor TEXT NOT NULL)"
DDL_PRODUCTOS = "CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL, descripcion TEXT NOT NULL, precio REAL NOT NULL CHECK (precio >= 0), categoria TEXT NOT NULL CHECK (categoria IN ('jocho','hamburguesa')), imagen_url TEXT, disponible INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0,1)))"
```

`init_db()` runs DDL, then for each table does `SELECT COUNT(*)`; if 0, `executemany` inserts 6 productos / 2 clientes / 6 config keys.

## 5. FastAPI Lifespan Sequence

1. `uvicorn app.main:app` imports `app/main.py`.
2. Lifespan startup → `init_db()` (creates DB, DDL, 14 seed rows).
3. `app.mount("/static", StaticFiles(directory="app/static"), name="static")`.
4. Module-level `templates = Jinja2Templates(directory="app/templates")`.
5. `app.include_router(public.router, prefix="")` + `admin.router, prefix="/admin"`.
6. Server binds `127.0.0.1:8000`; logs "Application startup complete".
7. `GET /healthz` → 200 `{"status": "ok"}`.

## 6. CSS Architecture

`tokens.css` = one `:root` block: 7 colors, 2 fonts, 8 spacing, 4 radius, 3 shadows. Google Fonts `<link>` in `base.html` (preconnect + parallel fetch, not `@import`). `main.css` = minimal reset + typography: `body` uses `--font-body` on `--color-azul-rey`; `h1–h6` use `--font-display`, `text-transform: uppercase`, `letter-spacing: 0.02em`. Load order: `tokens.css` then `main.css`. Kebab-case classes; BEM-lite optional; change-002 adds more stylesheets alphabetically.

## 7. Models.py Type Contracts

```python
@dataclass(slots=True, frozen=True)
class Producto:
    id: int; sku: str; nombre: str; descripcion: str; precio: float
    categoria: Literal["jocho", "hamburguesa"]
    imagen_url: str | None; disponible: bool
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Producto":
        return cls(id=row["id"], sku=row["sku"], nombre=row["nombre"],
                   descripcion=row["descripcion"], precio=row["precio"],
                   categoria=row["categoria"], imagen_url=row["imagen_url"],
                   disponible=bool(row["disponible"]))
```

Same `from_row` pattern for `Cliente { id, nombre, telefono, edad, genero: Literal["M","F","Otro"] }`, `ConfigKey { llave, valor }`, `OrdenLine { id, numero_orden, cliente_id, sku, producto, precio, cantidad, fecha_hora }`. Frozen + slots = immutable, low overhead. `disponible` INTEGER 0/1 maps to `bool` only at `from_row`.

## 8. Key Decisions and Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | None — raw `sqlite3` | Transparency, no dep overhead |
| `disponible` storage | INTEGER 0/1 → `bool` at `from_row` | SQLite has no native bool |
| Static files | `StaticFiles(directory="app/static")` | Built-in, zero deps |
| Templates | `Jinja2Templates(directory="app/templates")` | FastAPI-native |
| DB file path | `./el_perro_wero.db` | Easy dev access; gitignored |
| Startup hook | Lifespan context manager | Replaces deprecated `@app.on_event` |
| App name | `el-perro-wero` | kebab-case, pyproject convention |
| Python | 3.11+ | PEP 604 `X \| None`, `tomllib` |
| Admin router now | Mounted empty | Verifies `/admin` prefix routing in smoke test |
| Google Fonts | `<link>` in `base.html` | Preconnect, parallel fetch |
| Models | `@dataclass(slots=True, frozen=True)` | Immutable, no Pydantic dep yet |

## 9. Out-of-Scope (change-002)

Menu grid UI · cart · checkout · WhatsApp click-to-chat · admin login · inventory toggles · banner editor · orders table · real product images (placeholders only) · Facebook / DiDi Food buttons (URLs in DB, no UI) · Pydantic request models · first pytest tests.

## 10. Risks

- **Sync SQLite blocks event loop** on heavy writes — fine for MVP; change-002 may need `aiosqlite` or `run_in_executor`.
- **No connection pooling** — fine single-process; don't scale horizontally.
- **No Pydantic** — `models.py` wraps DB rows only; form input is change-002.
- **Google Fonts CDN** — offline falls back to Impact/system-ui per `--font-display` stack.
- **No automated tests yet** — `pyproject.toml` lists pytest/httpx but `tests/` is empty; smoke is manual (`uvicorn` + `curl /healthz`); change-002 writes the first test.
