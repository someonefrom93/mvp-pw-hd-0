# Change 005 — Admin UI

> Third and final sub-change of the umbrella `change-002-features` (see `../change-002-features/proposal.md`). Lands after `change-004-cart-whatsapp` and is the last in the stacked-to-main chain. Closes the public MVP loop: customers can now order, and the admin can now manage the business.

## Intent

Adds the hidden admin panel for "Jochos El Perro Wero": password login (text password `wero123`), signed cookie session via `itsdangerous`, inventory panel to toggle Sold Out per SKU, banner editor to update the promo text in real time, and an orders viewer that shows the most recent orders. The admin lives at `/admin/*` and is gated by an auth middleware.

After this change lands, the business owner can: visit `/admin/login`, log in with `wero123`, see the dashboard, toggle Sold Out for a product, update the banner text, and see new orders appear in the orders table as customers place them.

## Scope (this change only)

### In
- `app/auth.py` (NEW) — password check, signed cookie session helpers (`create_session_token`, `verify_session_token`, `require_admin` dependency)
- `app/schemas.py` (modified) — add `AdminLogin`, `BannerUpdate` Pydantic models
- `app/routes/admin.py` (modified) — 7 routes:
  - `GET /admin/login` — login form
  - `POST /admin/login` — validate password, set signed cookie, redirect to `/admin/`
  - `GET /admin/logout` — clear cookie, redirect to `/admin/login`
  - `GET /admin/` — dashboard (placeholder, just a welcome + link to other sections)
  - `GET /admin/inventario` — list products with their `disponible` state
  - `POST /admin/inventario/{sku}/toggle` — flip `disponible` for that SKU
  - `GET /admin/banner` — banner editor form (current value pre-filled)
  - `POST /admin/banner` — update `configuracion.banner_promocion`
  - `GET /admin/ordenes` — list of recent orders (last 50, ordered by fecha_hora DESC)
- `app/templates/admin/login.html` (NEW) — password form
- `app/templates/admin/dashboard.html` (NEW) — admin home with 3 nav cards
- `app/templates/admin/inventario.html` (NEW) — list of products with toggle buttons
- `app/templates/admin/banner.html` (NEW) — text input for the banner
- `app/templates/admin/ordenes.html` (NEW) — table of recent orders
- `app/templates/base_admin.html` (modified) — extends `base.html` with admin topbar (already exists from foundation; we'll add a logout button and active link highlighting)
- `app/static/css/admin.css` (NEW) — admin-specific styles (compact tables, toggle switches, form layouts for admin)
- `pyproject.toml` (no change — `itsdangerous` was already added in change-003 for forward compat)

### Out (NOT in this change)
- Real product images
- Image upload (admin can't change product photos)
- Order status updates / fulfillment tracking
- Multi-admin / role-based access
- Email / SMS notifications
- Analytics / tracking
- Password reset (single text password is fine for MVP)

## Approach

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth mechanism | Signed cookie with `itsdangerous.TimestampSigner` | No DB session table; tamper-resistant; stdlib-friendly |
| Password storage | Plain text comparison against constant `wero123` | Acceptable for single-admin local MVP; documented as known limitation |
| Cookie name | `wero_admin` | Namespaced to avoid collisions with other cookies |
| Cookie max-age | 7 days (`max_age=7*24*60*60`) | Long enough to not annoy the admin; short enough to limit exposure if cookie leaks |
| Cookie flags | `httponly=True, secure=False (local dev), samesite="lax"` | HTTP-only prevents XSS; samesite lax is fine for same-origin admin |
| Login form | Plain HTML form (no JS) | Simplest; works without JS |
| Session token | `itsdangerous.TimestampSigner(secret).sign("admin")` returns b64url-encoded signed string | Standard pattern; no DB lookup needed |
| Auth middleware | FastAPI `Depends(get_current_admin)` | DRY; one place to enforce auth; redirects to login if not authenticated |
| Banner update | Direct SQL `UPDATE` with `INSERT OR IGNORE` if config key missing | Idempotent; works even if config row was deleted |
| Orders viewer | Read-only table, no pagination for v1 | Last 50 orders is enough for an MVP |
| Order sort | `ORDER BY fecha_hora DESC` (newest first) | Natural for "recent orders" |
| Inventory toggle | `POST` endpoint per SKU with redirect back to inventario | Standard pattern; works with or without JS |
| Admin navigation | Topbar with links to /admin/, /admin/inventario, /admin/banner, /admin/ordenes, /admin/logout | One place for the admin to navigate |
| Logout | `GET /admin/logout` (not POST) | Simpler; no CSRF risk for an MVP; standard for admin panels |
| Image strategy | Not in scope (deferred) | Real product images can come in a future change |

## Capabilities

### New Capabilities
- `admin-auth`: password check, signed cookie session, `require_admin` dependency, login/logout routes
- `admin-ui`: dashboard, inventory panel, banner editor, orders viewer

### Modified Capabilities
- None — the foundation, change-003, and change-004 specs are not modified

## Affected Areas

| Area | Impact |
|------|--------|
| `app/auth.py` | New — ~50 LOC (password check + signed cookie helpers + dependency) |
| `app/schemas.py` | Modified — +2 Pydantic models (~15 LOC) |
| `app/routes/admin.py` | Modified — 7 routes + auth dependency wiring (~150 LOC) |
| `app/templates/admin/login.html` | New — ~25 LOC |
| `app/templates/admin/dashboard.html` | New — ~30 LOC |
| `app/templates/admin/inventario.html` | New — ~40 LOC |
| `app/templates/admin/banner.html` | New — ~25 LOC |
| `app/templates/admin/ordenes.html` | New — ~35 LOC |
| `app/templates/base_admin.html` | Modified — add logout link + active-link highlighting (~15 LOC added) |
| `app/static/css/admin.css` | New — ~80 LOC (compact tables, toggle switches, admin form layout) |
| `app/main.py` | No change (admin router already mounted at /admin) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Plain text password is insecure | Low for MVP | Single-admin local app; documented as known limitation; recommend bcrypt for production |
| Signed cookie secret is not rotated | Low for MVP | `SECRET_KEY` defaults to a stable string; can be overridden via env var in production |
| Order of route registration matters | Low | `app/main.py` already mounts admin router with prefix `/admin`; we just add routes to it |
| Orders viewer might be slow for large tables | Very low | v1 caps at 50 rows; pagination deferred |
| Banner update breaks the home page if text is too long | Low | `VARCHAR(500)`-style limit; template has `text-overflow: ellipsis` fallback |
| Toggle endpoint is unauthenticated (broken auth) | Low | `require_admin` dependency on every admin route |
| Static files (admin.css) served from `/static/css/` | Low | Same mount as foundation; works out of the box |
| Session cookie not cleared on logout | Low | Logout route sets `delete_cookie("wero_admin")` |

## Rollback Plan

Revert the merge commit on `main`. The app returns to the post-change-004 state (public UI works, no admin). No data loss — the admin only writes to `productos.disponible` and `configuracion.banner_promocion`, both of which are already valid data.

## Dependencies

- `itsdangerous>=2.1` (already added in `change-003-public-ui` for forward compat; no new install)
- All Python deps already in `pyproject.toml`

## Success Criteria

- [ ] `GET /admin/login` returns 200 with the password form
- [ ] `POST /admin/login` with `wero123` sets a signed cookie and redirects to `/admin/`
- [ ] `POST /admin/login` with a wrong password returns 200 with an error message (and the cookie is NOT set)
- [ ] `GET /admin/` without a cookie redirects to `/admin/login`
- [ ] `GET /admin/` with a valid cookie returns 200 with the dashboard
- [ ] `GET /admin/inventario` lists all 6 seed products with their `disponible` toggle state
- [ ] `POST /admin/inventario/JO-001/toggle` flips `disponible` for that SKU and redirects back
- [ ] After a toggle, the public home page reflects the change (Sold Out badge appears for `disponible=0`)
- [ ] `GET /admin/banner` shows a form pre-filled with the current `banner_promocion`
- [ ] `POST /admin/banner` updates `configuracion.banner_promocion` and redirects back
- [ ] After a banner update, the public home page shows the new banner text immediately
- [ ] `GET /admin/ordenes` shows the last 50 orders ordered by fecha_hora DESC
- [ ] `GET /admin/logout` clears the cookie and redirects to `/admin/login`
- [ ] All admin pages use `base_admin.html` and the magenta/yellow Mexican urban identity
- [ ] `mypy app/` is clean
- [ ] `ruff check app/` is clean

## Cross-references

- **Umbrella proposal**: `../change-002-features/proposal.md` (full UI scope + the 3-way split)
- **Previous changes**:
  - `../change-003-public-ui/` (UI shell, on main)
  - `../change-004-cart-whatsapp/` (transactional layer, on main)
  - `../archive/2026-06-07-change-001-foundation/` (base templates, base_admin.html)
- **Foundation specs**: `../../specs/{app-skeleton,base-templates,db-schema}/spec.md`
- **Existing main specs** (already on main):
  - `../../specs/db-schema/spec.md` — has `productos.disponible` column that admin toggles
  - `../../specs/public-ui/spec.md` — describes the banner (admin edits this text)
  - `../../specs/cart-flow/spec.md` — describes the order data (admin views this)
