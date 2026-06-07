# Tasks — Change 001 Foundation

> High-level outline only. Final breakdown by `sdd-tasks`.

| # | Task | Deliverable |
|---|------|-------------|
| T1 | Project skeleton | `pyproject.toml`, `app/__init__.py`, `app/main.py`, `.gitignore` update |
| T2 | SQLite schema + init_db() | `app/db.py` with DDL + `init_db()` + seed data (products, customers, config) |
| T3 | FastAPI app + /healthz | `app/main.py` wires routes; `app/routes/public.py` serves `GET /healthz` |
| T4 | Jinja2 base templates | `app/templates/base.html`, `app/templates/base_admin.html` |
| T5 | Design tokens | `app/static/css/tokens.css` (CSS custom properties, Google Fonts import), `app/static/css/main.css` (reset + typography) |
| T6 | Static assets layout | `app/static/js/.gitkeep`, `app/static/img/.gitkeep` |
| T7 | Smoke test | `uvicorn app.main:app` boots, `/healthz` responds 200, DB seed verifies |
| T8 | Changelog / README | Run instructions in `README.md` |

## Review Workload Forecast

- **Estimated changed lines**: ~300–380 (within 400-line budget)
- **Risk**: Low — no user-facing behavior, no auth, no state management
- **Strategy**: Single PR, work-unit commits per T1…T8
