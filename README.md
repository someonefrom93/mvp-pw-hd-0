# Jochos El Perro Wero — Hot Dogs & Hamburguesas

Local web app for Jochos El Perro Wero, a Mexican street-food restaurant
specializing in hot dogs (jochos) and hamburgesas. Built with FastAPI,
SQLite, Jinja2 templates, and vanilla JS + custom CSS.

## Requirements

- Python 3.11+

## Installation

```bash
pip install -e ".[dev]"
```

This installs runtime dependencies (FastAPI, uvicorn, Jinja2, python-multipart)
and dev dependencies (pytest, pytest-cov, httpx, ruff, mypy).

## Run

```bash
uvicorn app.main:app --reload
```

The app starts on `http://127.0.0.1:8000`. On first startup it initializes
the SQLite database (`el_perro_wero.db`) and seeds the menu + config data.

## Smoke Tests

```bash
# Start server in background
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
sleep 2

# Health check
curl http://127.0.0.1:8000/healthz
# Expect: {"status":"ok"}

# Static CSS
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/css/tokens.css
# Expect: 200

# Admin route (empty, returns 404)
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/admin/
# Expect: 404
```

## Project Structure

```
el-perro-wero-hotdogsAndBurgers-1/
├── pyproject.toml
├── README.md
├── el_perro_wero.db          (runtime, gitignored)
└── app/
    ├── __init__.py
    ├── main.py                (FastAPI app, lifespan, routers)
    ├── db.py                  (SQLite DDL, seed data, get_db)
    ├── models.py             (typed wrappers for DB rows)
    ├── routes/
    │   ├── __init__.py
    │   ├── public.py          (GET /healthz)
    │   └── admin.py           (/admin prefix router, empty)
    ├── templates/
    │   ├── base.html          (public HTML5 shell)
    │   └── base_admin.html    (admin shell, extends base)
    └── static/
        ├── css/
        │   ├── tokens.css     (design tokens: colors, fonts, spacing)
        │   └── main.css       (reset + typography)
        ├── js/.gitkeep
        └── img/.gitkeep
```

Full technical design: `openspec/changes/change-001-foundation/design.md`

## License

MIT