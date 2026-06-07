# Tasks: Change 001 — Foundation

> Expanded from T1-T8 outline. Each task is independently commitable. **T2 (db + models) was split out into `change-002-db-seed` for PR review hygiene — see "PR Split Strategy" below.**

## Task Dependency Graph (this change only)

```
T1 (skeleton) → T3 (app) → T4 (templates)
                ↓         → T5 (css)
              T6 (static) → T7 (smoke test)
                ↓
              T8 (docs)
```

T1 is the only blocker. T3–T6 can be done in any order after T1. T7 verifies everything. T8 last.

> **Note on init_db wiring**: The `app-skeleton` spec requires `init_db()` to run on startup. In the **stacked-to-main** PR order, `change-002-db-seed` lands FIRST, so the lifespan in `app/main.py` can safely `from app.db import init_db`. The lifespan call is in this change (T3) but is **gated** — it will only resolve once `change-002-db-seed` is merged. This is the standard pattern for stacked PRs: the second PR references symbols introduced by the first.

## T1: Project Skeleton
**Files**: `pyproject.toml`, `app/__init__.py`, `app/main.py` (stub), `.gitignore` (update)
**Depends on**: none
**Lines estimate**: ~50
**Status**: ✅ COMPLETE
**Acceptance**:
- `pyproject.toml` declares runtime + dev deps from app-skeleton spec
- `app/__init__.py` exists and is empty
- `app/main.py` has a minimal `app = FastAPI()` placeholder (full lifespan in T3)
- `.gitignore` adds `el_perro_wero.db` and `__pycache__/`
- `pip install -e .` succeeds

## T3: FastAPI App Wiring
**Files**: `app/main.py` (full), `app/routes/__init__.py`, `app/routes/public.py`, `app/routes/admin.py`
**Depends on**: T1
**Lines estimate**: ~60
**Status**: ✅ COMPLETE
**Acceptance**:
- `app/main.py` uses `@asynccontextmanager` lifespan that **imports and calls `init_db()` from `app.db`** — this resolves once `change-002-db-seed` lands; until then, `app/db.py` does not exist and the import will fail. **This is expected for stacked-to-main PRs.** sdd-verify of the merged main branch will confirm wiring.
- Static files mounted at `/static` from `app/static/`
- Jinja2Templates initialized with directory `app/templates/`
- `public.router` included with prefix `""` (root) — router has `GET /healthz`
- `admin.router` included with prefix `"/admin"`
- `GET /healthz` returns `{"status": "ok"}` with 200
- `uvicorn app.main:app` boots without traceback **after** `change-002-db-seed` is merged

## T4: Base Templates
**Files**: `app/templates/base.html`, `app/templates/base_admin.html`
**Depends on**: T1
**Lines estimate**: ~70
**Status**: ✅ COMPLETE
**Acceptance**:
- `base.html` has HTML5 doctype, lang="es-MX", charset, viewport meta, title block, Google Fonts link, tokens.css and main.css links, extra_head block, content block, footer block, extra_scripts block
- `base_admin.html` extends `base.html`, overrides title to "Admin · Jochos El Perro Wero", has topbar placeholder, admin_content and admin_scripts blocks
- A temporary `GET /__test_base` returns `templates.TemplateResponse(request, "base.html", {})` successfully (remove this test route after smoke test) — **omitted**: templates verified directly via Jinja2 Environment, no HTTP route needed

## T5: Design Tokens CSS
**Files**: `app/static/css/tokens.css`, `app/static/css/main.css`
**Depends on**: T1
**Lines estimate**: ~80
**Status**: ✅ COMPLETE
**Acceptance**:
- `tokens.css` defines all 9 colors, 2 fonts, 8 spacing vars, 4 radius vars, 3 shadow vars on `:root` (from design-tokens spec)
- `main.css` has the minimal reset and typography rules from design-tokens spec
- `curl http://127.0.0.1:8000/static/css/tokens.css` returns 200 with the tokens content

## T6: Static Assets Layout
**Files**: `app/static/js/.gitkeep`, `app/static/img/.gitkeep`
**Depends on**: T1
**Lines estimate**: ~2
**Status**: ✅ COMPLETE
**Acceptance**:
- Both directories exist
- `.gitkeep` files committed
- Static mount in T3 serves the directories (no 404 on `GET /static/js/` and `GET /static/img/`)

## T7: Smoke Test
**Files**: (no new files; manual verification)
**Depends on**: T1, T3, T4, T5, T6
**Lines estimate**: 0
**Status**: ✅ COMPLETE
**Acceptance**:
- `uvicorn app.main:app` starts on port 8000 (requires `change-002-db-seed` to be merged first)
- `curl -i http://127.0.0.1:8000/healthz` returns 200 `{"status":"ok"}`
- `curl -i http://127.0.0.1:8000/static/css/tokens.css` returns 200 with CSS content
- `curl -i http://127.0.0.1:8000/admin/` returns 404 (router mounted, no route yet — expected)
- The temporary `GET /__test_base` route from T4 is REMOVED before commit
- **DB verification** (4 tables + seed counts) is part of `change-002-db-seed`'s T2 acceptance, not this change

## T8: README
**Files**: `README.md`
**Depends on**: T1-T7
**Lines estimate**: ~40
**Status**: ✅ COMPLETE
**Acceptance**:
- `README.md` has sections: Project description, Requirements (Python 3.11+), Installation (`pip install -e .`), Run (`uvicorn app.main:app --reload`), Test commands (smoke checks), Project structure (link to design.md file tree), License (MIT placeholder)

## Total Estimate (this change only — T2 is in change-002)

| Task | LOC |
|------|-----|
| T1   | 50  |
| T3   | 60  |
| T4   | 70  |
| T5   | 80  |
| T6   | 2   |
| T7   | 0   |
| T8   | 40  |
| **TOTAL** | **~302** |

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | **~302** |
| Budget | 400 |
| Over budget? | **No — under by ~98 lines** |
| Risk | Low — no auth, no business logic, no DB, no Pydantic |
| Recommendation | **Single PR, no `size:exception` needed** |

## PR Split Strategy — `stacked-to-main`

This change is split from `change-002-db-seed` for review hygiene. The PR order is:

1. **PR #1** — `change-002-db-seed` (~150 LOC) — `app/db.py`, `app/models.py`, DDL, seed data, and the lifespan wiring update
2. **PR #2** — `change-001-foundation` (this change, ~302 LOC) — skeleton, app wiring (references symbols from PR #1), templates, CSS, static, smoke test, README

Both PRs target `main` directly. PR #2's base branch is `main` AFTER PR #1 merges, so `app/db.py` exists by the time PR #2's CI runs.

## Commit Strategy (work-unit commits for this change)

- Commit 1: T1 (skeleton)
- Commit 2: T3 (app wiring — references init_db from change-002, will be no-op until then)
- Commit 3: T4 (templates)
- Commit 4: T5 (css)
- Commit 5: T6 (static layout)
- Commit 6: T7 (smoke test verification only — done on the merged main, not on this branch in isolation)
- Commit 7: T8 (README)

Each commit is independently revertable. The app boots only after commits 1+2 land AND `change-002-db-seed` is merged first.

## Cross-references

- **Spec for db layer**: `../change-002-db-seed/specs/db-schema/spec.md` (canonical location; the copy in this change's `specs/db-schema/spec.md` is identical and will be archived alongside the db-seed change)
- **Design for db layer**: `../change-002-db-seed/design.md`

> T1-T8 completed: 2026-06-07 by sdd-apply
