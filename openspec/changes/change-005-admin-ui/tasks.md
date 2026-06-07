# Tasks: Change 005 — Admin UI

> Third and final sub-change of the umbrella `change-002-features`. ~345 LOC, under 400-line budget. Closes the public MVP loop: customers can order, admin can manage.

## Task Dependency Graph

```
T1 (auth helpers + schemas) → T2 (login route) → T3 (logout) → T4 (dashboard)
                                                          → T5 (inventario)
                                                          → T6 (toggle)
                                                          → T7 (banner form)
                                                          → T8 (banner update)
                                                          → T9 (orders viewer)
T10 (admin templates) — parallel with T2-T9 (uses T1's auth dep)
T11 (admin CSS) — parallel
T12 (smoke test) — verifies everything
```

T1 is the foundation (auth helpers + Pydantic models). T2-T9 are route handlers (each depends on T1's auth). T10-T11 are templates and CSS (can be done in parallel). T12 verifies end-to-end.

## T1: Auth Helpers + Pydantic Models
**Files**: `app/auth.py` (new), `app/schemas.py` (modified)
**Depends on**: none
**Lines estimate**: ~70
**Acceptance**:
- `app/auth.py` defines `ADMIN_PASSWORD = "wero123"`, `SECRET_KEY` (env-overridable), `_signer`, `check_password`, `create_session_token`, `verify_session_token`, `get_current_admin`
- `app/schemas.py` adds `AdminLogin(password: str)` and `BannerUpdate(banner_text: str, max_length=500)`
- `python3 -c "from app.auth import ADMIN_PASSWORD, check_password, create_session_token, verify_session_token; t = create_session_token(); assert verify_session_token(t); assert not check_password('wrong'); print('OK')"` succeeds
- Uses `secrets.compare_digest` for timing-attack-safe comparison

## T2: Login Routes
**Files**: `app/routes/admin.py` (modified — add `login_form` and `login_submit`)
**Depends on**: T1
**Lines estimate**: ~30
**Acceptance**:
- `GET /admin/login` returns 200 with `admin/login.html` (or 303 → /admin/ if already authenticated)
- `POST /admin/login` with `password=wero123` sets the `wero_admin` cookie (HttpOnly, Max-Age=604800, Path=/, SameSite=Lax) and returns 303 → /admin/
- `POST /admin/login` with wrong password returns 200 with the form re-rendered, showing "Contraseña incorrecta"
- `curl -c /tmp/cookies.txt -X POST http://127.0.0.1:8000/admin/login -d "password=wero123"` shows the cookie in `/tmp/cookies.txt`

## T3: Logout Route
**Files**: `app/routes/admin.py` (modified — add `logout`)
**Depends on**: T1
**Lines estimate**: ~10
**Acceptance**:
- `GET /admin/logout` clears the `wero_admin` cookie and returns 303 → /admin/login
- `curl -b /tmp/cookies.txt -c /tmp/cookies2.txt http://127.0.0.1:8000/admin/logout` shows the cookie removed in `/tmp/cookies2.txt`

## T4: Dashboard Route
**Files**: `app/routes/admin.py` (modified — add `dashboard`), `app/templates/admin/dashboard.html` (new)
**Depends on**: T1
**Lines estimate**: ~60
**Acceptance**:
- `GET /admin/` with auth returns 200 with the dashboard HTML
- The dashboard has 3 nav cards: Inventario, Banner, Órdenes
- `GET /admin/` without auth returns 303 → /admin/login
- `dashboard.html` extends `base_admin.html`

## T5: Inventario Route
**Files**: `app/routes/admin.py` (modified — add `inventario`), `app/templates/admin/inventario.html` (new)
**Depends on**: T1
**Lines estimate**: ~75
**Acceptance**:
- `GET /admin/inventario` with auth returns 200 listing all 6 products in a table
- Each row shows: sku, nombre, categoria, precio, disponible state, toggle button
- `?updated=JO-001` query param triggers a flash message
- Without auth: 303 → /admin/login
- `inventario.html` extends `base_admin.html`

## T6: Inventario Toggle Route
**Files**: `app/routes/admin.py` (modified — add `toggle_inventario`)
**Depends on**: T1
**Lines estimate**: ~15
**Acceptance**:
- `POST /admin/inventario/JO-001/toggle` flips `disponible` for that SKU and returns 303 → /admin/inventario?updated=JO-001
- After the toggle, the DB has the new value
- The home page reflects the change immediately

## T7: Banner Form Route
**Files**: `app/routes/admin.py` (modified — add `banner_form`), `app/templates/admin/banner.html` (new)
**Depends on**: T1
**Lines estimate**: ~55
**Acceptance**:
- `GET /admin/banner` with auth returns 200 with a form pre-filled with the current `configuracion.banner_promocion`
- Without auth: 303 → /admin/login
- `?updated=1` query param triggers a flash message
- `banner.html` extends `base_admin.html`

## T8: Banner Update Route
**Files**: `app/routes/admin.py` (modified — add `banner_update`)
**Depends on**: T1
**Lines estimate**: ~20
**Acceptance**:
- `POST /admin/banner` with `banner_text=...` updates `configuracion.banner_promocion` (using `INSERT ... ON CONFLICT DO UPDATE`) and returns 303 → /admin/banner?updated=1
- The home page shows the new banner text immediately
- Empty or very long text returns 422 (Pydantic validation via the implicit form binding)

## T9: Orders Viewer Route
**Files**: `app/routes/admin.py` (modified — add `ordenes`), `app/templates/admin/ordenes.html` (new)
**Depends on**: T1
**Lines estimate**: ~65
**Acceptance**:
- `GET /admin/ordenes` with auth returns 200 listing the last 50 orders (GROUP BY numero_orden, ORDER BY fecha_hora DESC)
- Each row shows: numero_orden, fecha_hora, customer name, total, num items, link to the WhatsApp redirect
- Without auth: 303 → /admin/login
- `ordenes.html` extends `base_admin.html`

## T10: Admin Templates (parallel with T2-T9)
**Files**: 5 new templates under `app/templates/admin/`
**Depends on**: T1 (for the auth dep)
**Lines estimate**: ~180
**Acceptance**:
- All 5 templates extend `base_admin.html`
- They use the Mexican urban identity (Magenta buttons, Yellow highlights, Bebas Neue/Anton for headings)
- The base_admin.html is updated to:
  - Include `<link rel="stylesheet" href="/static/css/admin.css">` after `components.css`
  - Add a topbar nav with links to Dashboard, Inventario, Banner, Órdenes, Salir
  - Highlight the active link based on `request.url.path`

## T11: Admin CSS
**Files**: `app/static/css/admin.css` (new)
**Depends on**: none
**Lines estimate**: ~80
**Acceptance**:
- File contains styles for `.admin-dashboard`, `.admin-nav-card`, `.admin-table`, `.toggle-button`, `.admin-form`, `.admin-flash`
- Uses CSS custom properties from `tokens.css`
- Compact, professional look (smaller padding than the public site's tables)
- `curl http://127.0.0.1:8000/static/css/admin.css` returns 200

## T12: Smoke Test (verification only, no new files)
**Files**: (no new files; manual verification)
**Depends on**: T1-T11
**Lines estimate**: 0
**Acceptance**:
- All 15+ smoke tests from `design.md` section 11 pass:
  - GET /admin/login (unauth) → 200
  - GET /admin/ (unauth) → 303 → /admin/login
  - POST /admin/login (wrong password) → 200 with error
  - POST /admin/login (correct password) → 303 → /admin/ with cookie set
  - GET /admin/ (auth) → 200
  - GET /admin/inventario (auth) → 200 with 6 products
  - POST /admin/inventario/JO-001/toggle → 303, DB updated
  - Home page reflects the toggle (Agotado badge)
  - GET /admin/banner → 200 with form pre-filled
  - POST /admin/banner → 303, DB updated
  - Home page shows the new banner
  - Place an order, GET /admin/ordenes → shows the order
  - GET /admin/logout → 303, cookie cleared
  - admin.css served with 200
- `mypy app/` is clean
- `ruff check app/` is clean

## Total Estimate

| Task | LOC |
|------|-----|
| T1   | 70  |
| T2   | 30  |
| T3   | 10  |
| T4   | 60  |
| T5   | 75  |
| T6   | 15  |
| T7   | 55  |
| T8   | 20  |
| T9   | 65  |
| T10  | 180 |
| T11  | 80  |
| T12  | 0   |
| **TOTAL** | **~660** |

> Note: this is higher than the design's 345 estimate because templates and CSS are more verbose when fully fleshed out. Still under the 400-line budget per PR if split into 2 sub-changes... but per the umbrella, this is one change. If applying trends > 500, consider splitting T10 (templates) and T11 (CSS) into a separate prep change.

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | **~660** |
| Budget | 400 |
| Over budget? | **Yes — by ~65%** |
| Risk | Low — no business logic, well-bounded admin pages, all structural |
| Recommendation | **Single PR with `size:exception`** |

**size:exception justification**:
> Admin UI change touches: 1 auth module (55 LOC), 2 Pydantic models (15 LOC), 7 admin routes (165 LOC), 5 admin templates (180 LOC), 1 admin CSS file (80 LOC), 1 modified base_admin.html (15 LOC). Total ~510 LOC of code + ~150 LOC of template/CSS markup. The bulk is HTML templates (40% of total) and CSS (15%), both static markup with minimal business logic. The actual Python code is ~245 LOC (auth + routes + schemas), well under 400.

## Commit Strategy (work-unit commits for this change)

- Commit 1: T1 (auth + schemas) — adds `app/auth.py` + modifies `app/schemas.py`
- Commit 2: T2 + T3 (login + logout) — adds the auth route handlers
- Commit 3: T4 (dashboard route) — adds the dashboard route
- Commit 4: T5 (inventario route) + T6 (toggle route) — adds the inventory routes
- Commit 5: T7 (banner form) + T8 (banner update) — adds the banner routes
- Commit 6: T9 (orders route) — adds the orders route
- Commit 7: T10 (templates) — adds the 5 admin templates + updates base_admin.html
- Commit 8: T11 (admin.css) — adds the admin CSS
- Commit 9: T12 (smoke test) — updates tasks.md to mark all done

Each commit is independently revertable. The app boots after commit 1 (auth helpers, no admin pages yet). The first admin page works after commits 1+2+7+8.

## PR Position in the Stacked-to-Main Chain

```
PR #1: change-001-foundation        (merged)
PR #2: change-003-public-ui         (merged)
PR #3: change-004-cart-whatsapp     (merged)
PR #4 (THIS CHANGE)                 change-005-admin-ui
```

This is the LAST change in the chain. After this lands, the public MVP is complete and ready for use.

## Cross-references

- **Spec**: `specs/{admin-auth,admin-ui}/spec.md`
- **Design**: `design.md`
- **Proposal**: `proposal.md`
- **Umbrella**: `../change-002-features/proposal.md`
