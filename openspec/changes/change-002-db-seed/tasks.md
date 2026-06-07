# Tasks: Change 002 — DB Seed

> Single-task change. T2 from the original change-001-foundation outline was split out for PR review hygiene (keeps each PR under 400 lines).

## Task Dependency Graph

```
T2 (db + models) — no dependencies, lands FIRST in stacked-to-main order
```

This change is a prerequisite for `change-001-foundation`'s lifespan wire-up.

## T2: Database Layer
**Files**: `app/db.py` (new), `app/models.py` (new)
**Depends on**: none
**Lines estimate**: ~150 (db.py ~120 + models.py ~60, minus shared boilerplate ≈ 150)
**Acceptance**:
- [x] `app/db.py` defines:
  - `DB_PATH = "el_perro_wero.db"`
  - `DDL_PRODUCTOS`, `DDL_CLIENTES`, `DDL_ORDENES`, `DDL_CONFIGURACION` string constants
  - `SEED_PRODUCTOS` (6 rows), `SEED_CLIENTES` (2 rows), `SEED_CONFIG` (6 key-value pairs)
  - `get_db()` context manager that sets `row_factory=sqlite3.Row` and `PRAGMA foreign_keys = ON`
  - `init_db()` that creates tables idempotently, seeds productos/clientes only if empty, and uses `INSERT OR IGNORE` for configuracion
- [x] `app/models.py` defines 4 frozen dataclasses (`Producto`, `Cliente`, `ConfigKey`, `OrdenLine`) each with a `from_row()` classmethod
- [x] `python -c "from app.db import init_db; init_db()"` creates `el_perro_wero.db` with 4 tables and 14 seed rows total
- [x] Calling `init_db()` a second time does not duplicate any seed row
- [x] `python -c "from app.models import Producto; from app.db import get_db; ..."` (smoke check) succeeds

**Smoke test commands** (to be run by the implementer):
```bash
# Fresh start
rm -f el_perro_wero.db
python -c "from app.db import init_db; init_db()"

# Verify tables
sqlite3 el_perro_wero.db ".tables"  # → clientes configuracion ordenes productos

# Verify seed counts
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM productos;"     # → 6
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM clientes;"      # → 2
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM configuracion;" # → 6

# Idempotency check
python -c "from app.db import init_db; init_db()"
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM productos;"     # → still 6

# Foreign keys check
sqlite3 el_perro_wero.db "PRAGMA foreign_keys;"  # → 0 (off by default in sqlite3 CLI)
python -c "from app.db import get_db
with get_db() as c:
    print(c.execute('PRAGMA foreign_keys').fetchone()[0])"  # → 1

# Model smoke check
python -c "
from app.db import get_db
from app.models import Producto
with get_db() as c:
    row = c.execute('SELECT * FROM productos WHERE sku = ?', ('JO-001',)).fetchone()
    p = Producto.from_row(row)
    assert p.sku == 'JO-001'
    assert p.categoria == 'jocho'
    assert p.disponible is True
    print('OK:', p.nombre, p.precio)
"
```

## Total Estimate

| Task | LOC |
|------|-----|
| T2   | ~150 |
| **TOTAL** | **~150** |

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | **~150** |
| Budget | 400 |
| Over budget? | **No — under by ~250 lines** |
| Risk | Low — pure data layer, no I/O race, no business logic |
| Recommendation | **Single PR, no `size:exception` needed** |

## Commit Strategy (work-unit commits for this change)

- Commit 1: `app/db.py` (full module — DDL, seed, get_db, init_db)
- Commit 2: `app/models.py` (full module — 4 dataclasses with from_row)

The two commits are independently revertable. The DB seed smoke test can run after commit 1 (db.py alone is enough to test the seed pipeline). Commit 2 adds the typed wrappers used by future route handlers.

## PR Position in the Stacked-to-Main Chain

```
PR #1 (THIS CHANGE) → change-002-db-seed      ~150 LOC
PR #2 (NEXT)        → change-001-foundation   ~302 LOC
```

This change must land FIRST. After it merges, `app/main.py` in change-001-foundation can safely `from app.db import init_db`.

## Cross-references

- **Spec**: `specs/db-schema/spec.md`
- **Design**: `design.md`
- **Proposal**: `proposal.md`
- **Companion change** (lands second): `../change-001-foundation/`

> T2 completed: 2026-06-07 by sdd-apply
