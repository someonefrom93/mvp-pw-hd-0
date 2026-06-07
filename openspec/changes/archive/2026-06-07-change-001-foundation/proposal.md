# Change 001 — Foundation

## Why

Downstream UI work (change-002-features) needs a running app, database, templates, and design tokens. This delivers the structural skeleton every later change depends on.

## What Changes

### In Scope
- `pyproject.toml` + `app/` package (`main.py`, `db.py`, `models.py`, `routes/`, `templates/`, `static/`)
- SQLite 3 tables: `clientes`, `ordenes`, `configuracion`; `init_db()` with seed data
- `GET /healthz`
- Jinja2 base templates: `base.html`, `base_admin.html`
- Design tokens CSS (`tokens.css` + `main.css`) with Bebas Neue + Anton from Google Fonts
- `static/js/`, `static/img/` with `.gitkeep`
- Dev deps: pytest, pytest-cov, httpx, ruff, mypy

### Out of Scope
Menu UI, cart, checkout, admin login, inventory, real images — all in change-002.

## Capabilities

### New Capabilities
- `db-schema`: SQLite DDL + `init_db()` with Mexican-Spanish seed data
- `app-skeleton`: FastAPI app, `/healthz` route, route module boundaries
- `design-tokens`: CSS custom properties (Royal Blue #1E3A8A / Magenta #EC4899 / Yellow #FACC15), spacing, radius, shadows, Bebas Neue + Anton fonts
- `base-templates`: Jinja2 inheritance chain (`base.html` → public, `base_admin.html` → admin)

### Modified Capabilities
None (greenfield)

## Approach

| Decision | Rationale |
|----------|-----------|
| Raw `sqlite3`, no ORM | MVP transparency; DB at `el_perro_wero.db` (gitignored) |
| Synchronous | Single-process local app |
| Jinja2 inheritance | Two shells; page templates extend them |
| Google Fonts CDN | `@import` in tokens.css |
| Thin wrappers in models.py | Keeps raw SQL honest |

**File tree**: `app/main.py`, `app/db.py`, `app/models.py`, `app/routes/public.py`, `app/routes/admin.py`, `app/templates/`, `app/static/`.

## Affected Areas

| Area | Impact |
|------|--------|
| `app/` package | New |
| `pyproject.toml` | New |
| `app/db.py`, `app/models.py` | New schema + wrappers |
| `app/routes/` | New route modules |
| `app/templates/` | New base templates |
| `app/static/css/` | New tokens + main CSS |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Raw SQL lacks type safety | Medium | models.py wrappers + mypy |
| SQLite multi-user unfit | Low | MVP is local-only |
| No admin auth yet | Low | Placeholder routes; auth in change-002 |

## Rollback Plan

Delete `app/`, `pyproject.toml`, `el_perro_wero.db`. Revert commit. Returns to sdd-init state.

## Dependencies

Python 3.11+, uvicorn, internet (Google Fonts CDN).

## Success Criteria

- [ ] `uvicorn app.main:app --reload` starts clean
- [ ] `GET /healthz` → 200 `{"status": "ok"}`
- [ ] `init_db()` creates 3 tables + seeds data
- [ ] `tokens.css` loads Bebas Neue + Anton fonts
- [ ] `base.html`, `base_admin.html` render without Jinja2 errors
