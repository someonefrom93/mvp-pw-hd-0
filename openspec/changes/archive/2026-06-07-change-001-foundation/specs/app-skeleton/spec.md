# Capability: app-skeleton

## Purpose
FastAPI application skeleton: package layout, dependencies, route module boundaries, static files, Jinja2 templates wiring, and a `/healthz` route that proves the app boots.

## ADDED Requirements

### Requirement: FastAPI app instance
The system MUST expose a FastAPI `app` instance importable as `app.main:app`.

### Requirement: package layout
The system MUST create the following package structure under `app/`:
- `app/__init__.py` (empty file, marks the package)
- `app/main.py` (FastAPI app, Jinja2 config, static mount, route registration)
- `app/db.py` (`get_db`, `init_db`, and DDL constants)
- `app/models.py` (typed wrappers for the seed data — typed dicts / dataclasses)
- `app/routes/__init__.py` (empty)
- `app/routes/public.py` (skeleton `APIRouter` — actual public routes in change-002)
- `app/routes/admin.py` (skeleton `APIRouter` — actual admin routes in change-002)

### Requirement: pyproject.toml runtime dependencies
The system MUST declare these runtime dependencies in `pyproject.toml` under `[project] dependencies` or `[tool.poetry.dependencies]`:
- `fastapi>=0.110`
- `uvicorn[standard]>=0.27`
- `jinja2>=3.1`
- `python-multipart>=0.0.9`

### Requirement: pyproject.toml dev dependencies
The system MUST declare these dev dependencies (PEP 621 optional-dependencies or poetry dev-dependencies):
- `pytest>=8.0`
- `pytest-cov>=4.1`
- `httpx>=0.27`
- `ruff>=0.5`
- `mypy>=1.10`

### Requirement: pyproject.toml metadata
The system MUST set in `pyproject.toml`:
- `name = "el-perro-wero"`
- `version = "0.1.0"`
- `requires-python = ">=3.11"`
- `description = "Local web app for Jochos El Perro Wero — Hot Dogs & Hamburguesas"`

### Requirement: static files mount
The system MUST mount static files at URL path `/static` serving from the local directory `app/static/`.

### Requirement: Jinja2 templates configuration
The system MUST configure Jinja2 templates directory at `app/templates/` and expose a module-level `templates` object built with `Jinja2Templates(directory="app/templates")` that route handlers can use.

### Requirement: route registration
The system MUST include the `public` and `admin` routers in `app/main.py` with prefixes:
- `public` router at prefix `""` (root)
- `admin` router at prefix `"/admin"`

(Routers are empty in this change; routes get added in change-002.)

### Requirement: init_db on startup
The system MUST call `init_db()` during FastAPI application startup (lifespan or startup event) so the database is always ready before the first request.

### Requirement: health-check route
The system MUST expose `GET /healthz` returning HTTP 200 with JSON body `{"status": "ok"}`.

### Requirement: local run command
Running `uvicorn app.main:app --reload` from the project root MUST start the server on `http://127.0.0.1:8000` with no traceback.

#### Scenario: app boots clean
- **GIVEN** a fresh checkout with `pyproject.toml` and `app/` in place
- **WHEN** `uvicorn app.main:app --reload` is run from the project root
- **THEN** the server starts on port 8000, the FastAPI startup logs show "Application startup complete", and no exception traceback appears

#### Scenario: healthz returns ok
- **GIVEN** the server is running
- **WHEN** `GET /healthz` is requested
- **THEN** the response is HTTP 200 with body `{"status": "ok"}` and `Content-Type: application/json`

#### Scenario: static css served
- **GIVEN** the server is running and `app/static/css/tokens.css` exists
- **WHEN** `GET /static/css/tokens.css` is requested
- **THEN** the response is HTTP 200 with `Content-Type: text/css` and the file body is returned

#### Scenario: init_db runs on startup
- **GIVEN** the database file does not exist
- **WHEN** the app starts and `GET /healthz` is called
- **THEN** after the request, `el_perro_wero.db` exists on disk and contains all 4 tables

#### Scenario: routers mounted at expected prefixes
- **GIVEN** the server is running
- **WHEN** `GET /admin/` is requested (or any `/admin/...` URL, even if it 404s)
- **THEN** the response comes from the admin router (not 404 from the public router) — verifiable by adding a temporary echo route in change-002

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
