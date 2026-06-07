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

## T1: Auth Helpers + Pydantic Models ✓
- [x] **COMPLETED** — `app/auth.py` (55 LOC) + `app/schemas.py` (+15 LOC)
**Files**: `app/auth.py` (new), `app/schemas.py` (modified)
**Depends on**: none
**Lines estimate**: ~70
**Acceptance**:
- [x] `app/auth.py` defines `ADMIN_PASSWORD = "wero123"`, `SECRET_KEY` (env-overridable), `_signer`, `check_password`, `create_session_token`, `verify_session_token`, `get_current_admin`
- [x] `app/schemas.py` adds `AdminLogin(password: str)` and `BannerUpdate(banner_text: str, max_length=500)`
- [x] `python3 -c "from app.auth import ...; ..."` succeeds
- [x] Uses `secrets.compare_digest` for timing-attack-safe comparison

## T2: Login Routes ✓
**Files**: `app/routes/admin.py` (modified — add `login_form` and `login_submit`)
**Depends on**: T1
**Lines estimate**: ~30
**Acceptance**:
- [x] `GET /admin/login` returns 200 with `admin/login.html` (or 303 → /admin/ if already authenticated)
- [x] `POST /admin/login` with `password=wero123` sets the `wero_admin` cookie (HttpOnly, Max-Age=604800, Path=/, SameSite=Lax) and returns 303 → /admin/
- [x] `POST /admin/login` with wrong password returns 200 with the form re-rendered, showing "Contraseña incorrecta"
- [x] Cookie is set correctly after successful login

## T3: Logout Route ✓
**Files**: `app/routes/admin.py` (modified — add `logout`)
**Depends on**: T1
**Lines estimate**: ~10
**Acceptance**:
- [x] `GET /admin/logout` clears the `wero_admin` cookie and returns 303 → /admin/login
- [x] Cookie is removed after logout

## T4: Dashboard Route ✓
**Files**: `app/routes/admin.py` (modified — add `dashboard`), `app/templates/admin/dashboard.html` (new)
**Depends on**: T1
**Lines estimate**: ~60
**Acceptance**:
- [x] `GET /admin/` with auth returns 200 with the dashboard HTML
- [x] The dashboard has 3 nav cards: Inventario, Banner, Órdenes
- [x] `GET /admin/` without auth returns 303 → /admin/login
- [x] `dashboard.html` extends `base_admin.html`

## T5: Inventario Route ✓
**Files**: `app/routes/admin.py` (modified — add `inventario`), `app/templates/admin/inventario.html` (new)
**Depends on**: T1
**Lines estimate**: ~75
**Acceptance**:
- [x] `GET /admin/inventario` with auth returns 200 listing all 6 products in a table
- [x] Each row shows: sku, nombre, categoria, precio, disponible state, toggle button
- [x] `?updated=JO-001` query param triggers a flash message
- [x] Without auth: 303 → /admin/login
- [x] `inventario.html` extends `base_admin.html`

## T6: Inventario Toggle Route ✓
**Files**: `app/routes/admin.py` (modified — add `toggle_inventario`)
**Depends on**: T1
**Lines estimate**: ~15
**Acceptance**:
- [x] `POST /admin/inventario/JO-001/toggle` flips `disponible` for that SKU and returns 303 → /admin/inventario?updated=JO-001
- [x] After the toggle, the DB has the new value
- [x] The home page reflects the change immediately

## T7: Banner Form Route ✓
**Files**: `app/routes/admin.py` (modified — add `banner_form`), `app/templates/admin/banner.html` (new)
**Depends on**: T1
**Lines estimate**: ~55
**Acceptance**:
- [x] `GET /admin/banner` with auth returns 200 with a form pre-filled with the current `configuracion.banner_promocion`
- [x] Without auth: 303 → /admin/login
- [x] `?updated=1` query param triggers a flash message
- [x] `banner.html` extends `base_admin.html`

## T8: Banner Update Route ✓
**Files**: `app/routes/admin.py` (modified — add `banner_update`)
**Depends on**: T1
**Lines estimate**: ~20
**Acceptance**:
- [x] `POST /admin/banner` with `banner_text=...` updates `configuracion.banner_promocion` (using `INSERT ... ON CONFLICT DO UPDATE`) and returns 303 → /admin/banner?updated=1
- [x] The home page shows the new banner text immediately
- [x] Empty or very long text returns 422 (Pydantic validation via the implicit form binding)

## T9: Orders Viewer Route ✓
**Files**: `app/routes/admin.py` (modified — add `ordenes`), `app/templates/admin/ordenes.html` (new)
**Depends on**: T1
**Lines estimate**: ~65
**Acceptance**:
- [x] `GET /admin/ordenes` with auth returns 200 listing the last 50 orders (GROUP BY numero_orden, ORDER BY fecha_hora DESC)
- [x] Each row shows: numero_orden, fecha_hora, customer name, total, num items
- [x] Without auth: 303 → /admin/login
- [x] `ordenes.html` extends `base_admin.html`

## T10: Admin Templates ✓
**Files**: 5 new templates under `app/templates/admin/`
**Depends on**: T1 (for the auth dep)
**Lines estimate**: ~180
**Acceptance**:
- [x] All 5 templates extend `base_admin.html`
- [x] They use the Mexican urban identity (Magenta buttons, Yellow highlights, Bebas Neue/Anton for headings)
- [x] `base_admin.html` includes admin.css link, topbar nav with active-link highlighting

## T11: Admin CSS ✓
**Files**: `app/static/css/admin.css` (new)
**Depends on**: none
**Lines estimate**: ~80
**Acceptance**:
- [x] File contains styles for `.admin-dashboard`, `.admin-nav-card`, `.admin-table`, `.toggle-button`, `.admin-form`, `.admin-flash`
- [x] Uses CSS custom properties from `tokens.css`
- [x] Compact, professional look
- [x] `curl http://127.0.0.1:8000/static/css/admin.css` returns 200

## T12: Smoke Test ✓
**Files**: (no new files; manual verification)
**Depends on**: T1-T11
**Lines estimate**: 0
**Acceptance**:
- [x] All smoke tests from `design.md` section 11 pass (11 capability tests verified)
- [x] Dashboard, inventario, banner, ordenes, login, logout all functional
- [x] Toggle updates DB and home page reflects change
- [x] Banner update persists and home page shows new banner
- [x] Order placed visible in admin/ordenes
- [x] admin.css served with 200

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

---

> T1–T12 completed: 2026-06-07 by sdd-apply. All 11 capability smoke tests passed. Admin panel is fully functional at `/admin/*`.
