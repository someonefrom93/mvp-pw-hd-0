# Tasks: Change 001 — Foundation

> Expanded from T1–T8 outline. Each task is independently commitable.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~452 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | Single PR with `size:exception` OR split T2 into separate change |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Project skeleton (T1) | PR1 | Independent; `pip install -e .` works after |
| 2 | DB layer + models (T2) | PR 2 | ~150 LOC; depends on T1 |
| 3 | App wiring (T3) | PR 3 | ~60 LOC; depends on T1+T2 |
| 4 | Base templates (T4) | PR 4 | ~70 LOC; depends on T1 |
| 5 | Design tokens CSS (T5) | PR 5 | ~80 LOC; depends on T1 |
| 6 | Static layout (T6) | PR 6 | ~2 LOC; depends on T1 |
| 7 | Smoke test (T7) | PR 7 | Verification only; no new files |
| 8 | README (T8) | PR 8 | ~40 LOC; depends on T1–T7 |

## Task Dependency Graph

```
T1 (skeleton) ──→ T2 (db)
                │
                ↓
 T3 (app) ──→ T7 (smoke test)
                │
                ↓
              T4 (templates) ──→ T5 (css)
                              ──→ T6 (static)
                              ──→ T8 (docs)
```

## T1: Project Skeleton

**Files**: `pyproject.toml`, `app/__init__.py`, `app/main.py` (stub), `.gitignore` (update)

**Depends on**: none

**Lines estimate**: ~50

**Acceptance**:
- `pyproject.toml` declares `name="el-perro-wero"`, `version="0.1.0"`, `requires-python=">=3.11"`, `description="Local web app for Jochos El Perro Wero — Hot Dogs & Hamburguesas"`
- Runtime deps: `fastapi>=0.110`, `uvicorn[standard]>=0.27`, `jinja2>=3.1`, `python-multipart>=0.0.9`
- Dev deps: `pytest>=8.0`, `pytest-cov>=4.1`, `httpx>=0.27`, `ruff>=0.5`, `mypy>=1.10`
- `app/__init__.py` exists and is empty
- `app/main.py` has a minimal `app = FastAPI()` placeholder (full lifespan in T3)
- `.gitignore` adds `el_perro_wero.db` and `__pycache__/`
- `pip install -e .` (or `pip install -r requirements.txt`) succeeds

## T2: Database Layer

**Files**: `app/db.py`, `app/models.py`

**Depends on**: T1

**Lines estimate**: ~150

**Acceptance**:
- `app/db.py` defines `DB_PATH` (`.`/`el_perro_wero.db`), 4 `DDL_*` constants, `SEED_PRODUCTOS` (6 items), `SEED_CLIENTES` (2 items), `SEED_CONFIG` (6 keys), `get_db()` context manager, `init_db()`
- `DDL_CLIENTES`: `CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, telefono TEXT NOT NULL, edad INTEGER NOT NULL, genero TEXT NOT NULL CHECK (genero IN ('M','F','Otro')))`
- `DDL_ORDENES`: `CREATE TABLE IF NOT EXISTS ordenes (id INTEGER PRIMARY KEY AUTOINCREMENT, numero_orden TEXT NOT NULL, cliente_id INTEGER NOT NULL REFERENCES clientes(id), sku TEXT NOT NULL, producto TEXT NOT NULL, precio REAL NOT NULL CHECK (precio >= 0), cantidad INTEGER NOT NULL CHECK (cantidad > 0), fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)`
- `DDL_CONFIG`: `CREATE TABLE IF NOT EXISTS configuracion (llave TEXT PRIMARY KEY, valor TEXT NOT NULL)`
- `DDL_PRODUCTOS`: `CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL, descripcion TEXT NOT NULL, precio REAL NOT NULL CHECK (precio >= 0), categoria TEXT NOT NULL CHECK (categoria IN ('jocho','hamburguesa')), imagen_url TEXT, disponible INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0,1)))`
- `get_db()` sets `row_factory = sqlite3.Row`, runs `PRAGMA foreign_keys = ON`, yields connection, closes on exit
- `init_db()` is idempotent (calls each DDL then `SELECT COUNT(*)` guard before each seed insert)
- Seed productos: JO-001/JOCHO CLÁSICO/$65/jocho, JO-002/JOCHO HAWAIANO/$75/jocho, JO-003/JOCHO ITALIANO/$85/jocho, HB-001/HAMB. SENCILLA/$90/hamburguesa, HB-002/HAMB. CON TOCINO/$110/hamburguesa, HB-003/HAMB. BBQ/$120/hamburguesa
- Seed clientes: "Juan Pérez" (5551234567, 28, M), "María López" (5559876543, 35, F)
- Seed config: `banner_promocion`, `horarios_texto`, `ubicacion_texto`, `whatsapp_numero`, `facebook_url`, `didi_food_url`
- `app/models.py` defines 4 `@dataclass(slots=True, frozen=True)`: `Producto` (id, sku, nombre, descripcion, precio, categoria: Literal["jocho","hamburguesa"], imagen_url: str|None, disponible: bool, from_row), `Cliente` (id, nombre, telefono, edad, genero: Literal["M","F","Otro"], from_row), `ConfigKey` (llave, valor, from_row), `OrdenLine` (id, numero_orden, cliente_id, sku, producto, precio, cantidad, fecha_hora, from_row)
- `python -c "from app.db import init_db; init_db()"` succeeds and creates `el_perro_wero.db` with 4 tables + seed rows

## T3: FastAPI App Wiring

**Files**: `app/main.py` (full), `app/routes/__init__.py`, `app/routes/public.py`, `app/routes/admin.py`

**Depends on**: T1, T2

**Lines estimate**: ~60

**Acceptance**:
- `app/main.py` uses `@asynccontextmanager` lifespan that calls `init_db()` on startup
- Static files mounted at `/static` from `app/static/`
- `Jinja2Templates(directory="app/templates")` at module level
- `public.router` included with prefix `""` (root)
- `admin.router` included with prefix `"/admin"`
- `public.py` exports `router` with `GET /healthz` returning `{"status": "ok"}` + 200
- `admin.py` exports `router` (empty placeholder)
- `uvicorn app.main:app` boots without traceback

## T4: Base Templates

**Files**: `app/templates/base.html`, `app/templates/base_admin.html`

**Depends on**: T1

**Lines estimate**: ~70

**Acceptance**:
- `base.html`: HTML5 doctype, `lang="es-MX"`, `<meta charset="UTF-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1.0">`, `<title>{% block title %}Jochos El Perro Wero{% endblock %}</title>`, Google Fonts preconnect + stylesheet link (Bebas Neue, Anton, Inter), `tokens.css` + `main.css` links, `{% block extra_head %}{% endblock %}`, `{% block content %}{% endblock %}`, `<footer>{% block footer %}{% endblock %}</footer>`, `{% block extra_scripts %}{% endblock %}`
- `base_admin.html`: `{% extends "base.html" %}`, overrides title to "Admin · Jochos El Perro Wero", has `<header class="admin-topbar">` placeholder, `{% block admin_content %}{% endblock %}`, `{% block admin_scripts %}{% endblock %}`
- A temporary `GET /__test_base` route (added in T3) returns `templates.TemplateResponse(request, "base.html", {})` successfully — REMOVE this route before committing T7

## T5: Design Tokens CSS

**Files**: `app/static/css/tokens.css`, `app/static/css/main.css`

**Depends on**: T1

**Lines estimate**: ~80

**Acceptance**:
- `tokens.css` has `:root` block with: 9 color vars (--color-azul-rey: #1E3A8A, --color-azul-rey-dark: #0F1E47, --color-magenta: #EC4899, --color-magenta-dark: #BE185D, --color-amarillo: #FACC15, --color-amarillo-dark: #CA8A04, --color-white: #FFFFFF, --color-text: #FFFFFF, --color-text-dark: #0F1E47), 2 font vars (--font-display: 'Bebas Neue', 'Anton', Impact, sans-serif; --font-body: 'Inter', system-ui, -apple-system, sans-serif), 8 spacing vars (--space-1: 4px through --space-8: 64px), 4 radius vars (--radius-sm: 6px, --radius-md: 12px, --radius-lg: 24px, --radius-pill: 999px), 3 shadow vars (--shadow-magenta, --shadow-amarillo, --shadow-azul)
- `main.css`: minimal reset (`*, *::before, *::after { box-sizing: border-box; }`, `body,h1..h6,p,ul,ol { margin:0; padding:0; }`, `ul,ol { list-style:none; }`, `img { display:block; max-width:100%; }`, `a { color:inherit; text-decoration:none; }`), `body` uses `var(--font-body)` + `var(--color-text)` + `background: var(--color-azul-rey)`, `h1..h6` use `var(--font-display)` + `text-transform: uppercase` + `letter-spacing: 0.02em`
- `curl http://127.0.0.1:8000/static/css/tokens.css` returns 200 with CSS content

## T6: Static Assets Layout

**Files**: `app/static/js/.gitkeep`, `app/static/img/.gitkeep`

**Depends on**: T1

**Lines estimate**: ~2

**Acceptance**:
- Both directories exist
- `.gitkeep` files committed
- `GET /static/js/` and `GET /static/img/` return 404 (empty dirs, no index), but the mount is active (no405)

## T7: Smoke Test

**Files**: (no new files; manual verification)

**Depends on**: T1–T6

**Lines estimate**: 0

**Acceptance**:
- `uvicorn app.main:app` starts on port 8000
- `curl -i http://127.0.0.1:8000/healthz` returns 200 `{"status":"ok"}`
- `curl -i http://127.0.0.1:8000/static/css/tokens.css` returns 200 with CSS content
- `sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM productos;"` returns 6
- `sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM clientes;"` returns 2
- `sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM configuracion;"` returns 6
- `curl -i http://127.0.0.1:8000/admin/` returns 404 (router mounted, no route yet — expected)
- The temporary `GET /__test_base` route from T4 is REMOVED before commit

## T8: README

**Files**: `README.md`

**Depends on**: T1–T7

**Lines estimate**: ~40

**Acceptance**:
- `README.md` has sections: Project description, Requirements (Python 3.11+), Installation (`pip install -e .`), Run (`uvicorn app.main:app --reload`), Test commands (smoke checks), Project structure (matches design.md file tree), License (MIT placeholder)

## Total Estimate

| Task | Lines |
|------|-------|
| T1 | ~50 |
| T2 | ~150 |
| T3 | ~60 |
| T4 | ~70 |
| T5 | ~80 |
| T6 | ~2 |
| T7 | 0 |
| T8 | ~40 |
| **TOTAL** | **~452** |

## Review Workload Flag

**~452 lines vs 400-line budget — over by ~52 lines (13%).**

- Risk is **Low** (no auth, no business logic, no Pydantic, no cross-cutting concerns)
- T2 (DB schema + seed) alone is ~150 LOC, driven by4 DDL statements with CHECK constraints and 14 seed rows
- All tasks are independently commitable and reviewable

**If user accepts `size:exception`**: proceed with single PR. Suggested justification text:

> "Foundation change touches DB layer (150 LOC) + FastAPI wiring (60 LOC) + CSS (80 LOC) + templates (70 LOC) + skeleton/docs (~90 LOC). All structural — no business logic, no auth, no Pydantic. Each task is independently commitable and reviewable. Total ~452 lines vs 400 budget; the overage is in the DB schema + seed (4 tables × 12 columns ≈ 80 lines of DDL alone)."

**If user rejects `size:exception`**: split into two changes:
- `change-001-foundation` (T1 skeleton + T3 app wiring + T4 templates + T5 CSS + T6 static + T7 smoke + T8 README) ≈ 300 LOC
- `change-002-db-seed` (T2 db.py + models.py + DDL + seed data) ≈ 150 LOC

## Commit Strategy (work-unit commits)

| Commit | Task | Message |
|--------|------|---------|
| 1 | T1 | `feat: project skeleton with pyproject.toml and app/ package` |
| 2 | T2 | `feat: SQLite schema, init_db, and typed row models` |
| 3 | T3 | `feat: FastAPI app wiring with lifespan, routers, and /healthz` |
| 4 | T4 | `feat: Jinja2 base templates (public + admin shells)` |
| 5 | T5 | `feat: design tokens CSS (colors, fonts, spacing, shadows)` |
| 6 | T6 | `feat: static assets directory layout` |
| 7 | T7 | `test: smoke test verification (manual curl + sqlite3 checks)` |
| 8 | T8 | `docs: README with run instructions and project structure` |
