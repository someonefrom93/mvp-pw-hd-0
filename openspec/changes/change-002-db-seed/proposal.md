# Change 002 — DB Seed

## Why

The foundation change (`change-001-foundation`) was sized at ~452 LOC including the database layer (`app/db.py` + `app/models.py` + DDL + seed). To keep both PRs under the 400-line review budget, the DB layer was split out into its own change. This also gives the DB schema and seed data a focused review surface (data shape is the most consequential decision in a data-driven MVP).

This change is the **base of the stacked-to-main PR pair**: it lands first, then `change-001-foundation` lands on top and references the `init_db()` symbol introduced here.

## What Changes

### In Scope
- `app/db.py` — `DB_PATH` constant, 4 `DDL_*` string constants, `SEED_PRODUCTOS` / `SEED_CLIENTES` / `SEED_CONFIG` data, `get_db()` context manager, `init_db()` function
- `app/models.py` — 4 typed dataclasses (`Producto`, `Cliente`, `ConfigKey`, `OrdenLine`) with `from_row()` classmethods
- **One-line update to `app/main.py`** — replace the lifespan body to actually call `init_db()` (this is the wire-up to change-001)
- 4 SQLite tables created idempotently on first run: `clientes`, `ordenes`, `configuracion`, `productos`
- Seed data: 6 products, 2 sample clients, 6 config rows — all Mexican-Spanish

### Out of Scope
- All FastAPI routes beyond the `init_db()` wire-up (in `change-001-foundation`)
- UI templates, CSS, static assets (in `change-001-foundation`)
- Real product images (placeholders only)
- Pydantic models, form validation (deferred to a future change when forms land)

## Capabilities

### New Capabilities
- `db-schema`: SQLite DDL + `init_db()` with Mexican-Spanish seed data (canonical home; `change-001-foundation` carries an identical copy that will archive together with this change)

### Modified Capabilities
- `app-skeleton` (in `change-001-foundation`): the lifespan body is updated here to call `init_db()`. **This is the only cross-cutting change** — one line in `app/main.py`.

## Approach

| Decision | Rationale |
|----------|-----------|
| Raw `sqlite3`, no ORM | MVP transparency; DB at `el_perro_wero.db` (gitignored) |
| Synchronous | Single-process local app |
| DDL as string constants | Easy to read, easy to test, no migration framework needed |
| Seed via INSERT OR IGNORE | Idempotent: re-running `init_db()` does not duplicate rows |
| Typed dataclasses with `from_row()` | Maps `sqlite3.Row` → typed Python object for route handlers in change-002; no ORM needed |
| `INTEGER 0/1` for `disponible` → `bool` in dataclass | SQLite has no native bool; standard pattern |
| Lifespan wire-up is one line | Minimal cross-cutting change to `change-001-foundation`'s `app/main.py` |

**File tree** (this change adds):
```
app/
├── db.py          (new)
└── models.py      (new)
```

**Modified file** (one line):
```
app/main.py        (lifespan body updated to call init_db())
```

## Affected Areas

| Area | Impact |
|------|--------|
| `app/db.py` | New — ~120 lines |
| `app/models.py` | New — ~60 lines |
| `app/main.py` | 1 line modified in lifespan |
| `el_perro_wero.db` | Created at runtime on first startup |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Cross-PR merge conflict on `app/main.py` | Low | The lifespan edit is 1 line; PR #1 (this) lands first, PR #2 (change-001) modifies the SAME lifespan line — git will detect the conflict and surface it; resolve by keeping the union of both edits |
| Raw SQL lacks type safety | Medium | models.py wrappers + mypy |
| Seed data drift from menu UI | Low | change-002-features will query the DB for products, not hardcode |
| Foreign keys not enforced by default | Low | `get_db()` sets `PRAGMA foreign_keys = ON` on every connect |
| Lifespan call fails if `init_db()` raises | Low | Startup log shows the error; uvicorn exits non-zero; the operator sees it immediately |

## Rollback Plan

Delete `app/db.py`, `app/models.py`, revert the one-line `app/main.py` lifespan change, delete `el_perro_wero.db`. Revert the merge commit on `main`. The app returns to change-001-foundation state with no DB layer.

## Dependencies

- Python 3.11+ stdlib (`sqlite3`, `contextlib`, `dataclasses`)
- No new third-party packages

## Success Criteria

- [ ] `python -c "from app.db import init_db; init_db()"` creates the DB and seeds all rows
- [ ] Calling `init_db()` a second time does not duplicate any seed row
- [ ] `sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM productos;"` returns 6
- [ ] `sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM clientes;"` returns 2
- [ ] `sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM configuracion;"` returns 6
- [ ] `python -c "from app.models import Producto; from app.db import get_db; ..."` (smoke check) succeeds
- [ ] After merging into main, `uvicorn app.main:app` starts cleanly and `/healthz` returns 200

## Cross-References

- Spec: `specs/db-schema/spec.md`
- Design: `design.md`
- Tasks: `tasks.md`
- Companion change: `../change-001-foundation/` (lands second in the stacked-to-main order)
