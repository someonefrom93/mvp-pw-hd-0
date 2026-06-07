# Change 002-Features — Full UI (Public + Admin)

> **Umbrella change**. This proposal covers the full ~800-1000 LOC UI work. To keep each PR under the 400-line review budget, this umbrella is split into 3 sub-changes that land in stacked-to-main order:
>
> - **`change-003-public-ui`** (~430-480 LOC) — public client UI SHELL: home page, banner, location, menu grid, social buttons, WeroCart object (vanilla JS, localStorage), component CSS for the Mexican urban identity, mascot SVG, product placeholders. **NO checkout yet.**
> - **`change-004-cart-whatsapp`** (~260-310 LOC) — transactional layer on top of change-003: Pydantic v2 schemas, `POST /ordenes` with atomic cliente upsert + ordenes insert, `GET /ordenes/{id}/whatsapp` redirect, `order.js` form handler, `order_pending.html`, WhatsApp message formatter.
> - **`change-005-admin-ui`** (~300-400 LOC) — admin login, inventory toggles, banner editor, orders viewer.
>
> PR order: PR #3 = `change-003-public-ui` (lands first), PR #4 = `change-004-cart-whatsapp` (lands second, depends on change-003's WeroCart and components.css), PR #5 = `change-005-admin-ui` (lands last, depends on all of the above).

## Why

The foundation (`change-001-foundation` + `change-002-db-seed`) gives us a working FastAPI app with the DB schema, design tokens, and base templates. But the app is still a blank shell — no public pages, no admin, no business logic. This change brings the brand to life with the Mexican urban identity (Azul Rey + Magenta + Amarillo) and the full user flow: customer browses menu, fills cart, confirms via WhatsApp; admin manages inventory and sees orders.

## What Changes

### In Scope (umbrella)
- **Public UI** (`/`):
  - Hero/dynamic promo banner (editable from admin)
  - Location/hours block (text + simulated map iframe)
  - Interactive menu grid (jochos + hamburguesas) loaded from `productos` table
  - "Sold Out" toggle effect (button shows "Agotado" when `disponible=0`)
  - Shopping cart (vanilla JS, localStorage-backed, quantity selectors)
  - Customer data form (nombre, teléfono, edad, género)
  - Order confirmation: POST `/ordenes` creates rows in `clientes` + `ordenes`, returns `wa.me/...` URL
  - Social media buttons (Facebook, DiDi Food) using config URLs
- **Admin UI** (`/admin`):
  - Login screen (`GET /admin/login` form, `POST /admin/login` validates `wero123` password, sets signed cookie session)
  - Inventory panel (`GET /admin/inventario`) with toggles per SKU writing to `productos.disponible`
  - Banner editor (`GET /admin/banner` form) updating `configuracion.banner_promocion`
  - Orders viewer (`GET /admin/ordenes`) with dataframe-style table of recent orders
- **Component CSS** (in `app/static/css/components.css`):
  - Buttons (`.btn`, `.btn-magenta`, `.btn-amarillo`, `.btn-outline`)
  - Cards (`.card`, `.card-producto`)
  - Hero / banner (`.hero-banner` with starburst)
  - Footer (`.site-footer` with social links)
  - Forms (`.form-input`, `.form-label`)
  - Modal (`.modal`)
  - Admin topbar (`.admin-topbar`)
- **Pydantic models** (in `app/schemas.py`):
  - `CartItem(sku, cantidad)`
  - `CustomerData(nombre, telefono, edad, genero)`
  - `OrderCreate(items: list[CartItem], customer: CustomerData)`
  - `OrderResponse(numero_orden, total, whatsapp_url)`
  - `AdminLogin(password)`
  - `BannerUpdate(banner_text)`

### Out of Scope (deferred to future changes)
- Real product images (still placeholders / `None`)
- Order tracking / status updates
- Payment integration
- Email / SMS notifications
- Customer accounts (only guest checkout in this MVP)
- Multi-admin / role-based access
- Analytics / tracking
- Database migrations (no alembic; schema is set in stone)
- Image upload (admin can't upload product photos)

## Sub-change Split — `change-003-public-ui` (PR #3)

### Scope
- All public UI SHELL: banner, location, menu grid, social buttons, customer form UI, WeroCart object (vanilla JS, localStorage), component CSS (`components.css`)
- `app/schemas.py` (NEW) — Pydantic models
- Routes in `app/routes/public.py`: `GET /` only (NOT the order endpoints)
- `app/templates/public/home.html` (NEW)
- `app/templates/public/partials/product_card.html`, `cart_summary.html` (NEW)
- `app/static/css/components.css` (NEW)
- `app/static/js/cart.js` (NEW) — WeroCart object
- `app/static/img/wero-mascot.svg` + 6 placeholder SVGs (NEW)
- `pyproject.toml` — add `itsdangerous` dep
- `app/templates/base.html` — add `<link>` to components.css (1 line)
- **NOT in scope (deferred to `change-004-cart-whatsapp`):** `POST /ordenes`, `GET /ordenes/{id}/whatsapp`, `app/static/js/order.js`, `app/templates/public/order_pending.html`, server-side order persistence, WhatsApp message formatter
- ~430-480 LOC

### Why split (first half)
- Static UI and transactional logic are independent review surfaces
- The WeroCart object can be tested visually in the browser without the order endpoint

### Stacked-to-main position
- Lands after `change-001-foundation` and `change-002-db-seed` are merged (already in main)
- Does NOT depend on `change-004-cart-whatsapp` or `change-005-admin-ui`

## Sub-change Split — `change-004-cart-whatsapp` (PR #4)

### Scope
- `app/schemas.py` (NEW, if not in change-003) — Pydantic v2 models
- Routes in `app/routes/public.py`: `POST /ordenes`, `GET /ordenes/{numero_orden}/whatsapp`
- `app/static/js/order.js` (NEW) — form submit handler that POSTs `/ordenes` and redirects to WhatsApp
- `app/templates/public/order_pending.html` (NEW) — "¡Gracias por tu pedido!" page
- `app/templates/public/partials/cart_summary.html` (MODIFIED) — add customer form fields
- Server-side: `format_order_message()` helper, `build_whatsapp_url()` helper, atomic transaction
- `app/static/img/wero-mascot.svg` (if not in change-003) — referenced in WhatsApp message
- ~260-310 LOC

### Why split (second half)
- Transactional logic (Pydantic validation, atomic DB writes, URL building) is a different review concern than visual UI
- Can be reviewed against scenarios that test the order flow end-to-end

### Stacked-to-main position
- Lands after `change-003-public-ui` is merged
- DEPENDS on `change-003-public-ui`'s WeroCart object and components.css
- Does NOT depend on `change-005-admin-ui`

## Sub-change Split — `change-005-admin-ui` (PR #5)

### Scope
- Admin login screen + signed cookie session middleware
- Inventory panel with toggles
- Banner editor
- Orders viewer
- Admin-only routes in `app/routes/admin.py`: `GET /admin/login`, `POST /admin/login`, `GET /admin/`, `GET /admin/inventario`, `POST /admin/inventario/{sku}/toggle`, `GET /admin/banner`, `POST /admin/banner`, `GET /admin/ordenes`, `GET /admin/logout`
- Pydantic models for `AdminLogin`, `BannerUpdate`
- ~300-400 LOC

### Why split
- Admin auth is a separate concern (cookie session, password handling)
- Can be reviewed independently of public UI

### Stacked-to-main position
- Lands after `change-003-public-ui` and `change-004-cart-whatsapp` are merged
- DEPENDS on the public UI's component CSS being in main

## Capabilities

### New Capabilities
- `public-ui`: banner, location, menu grid, cart, customer form, WhatsApp integration
- `admin-ui`: login, inventory, banner editor, orders viewer
- `component-css`: reusable UI components (buttons, cards, hero, footer, forms, modal)
- `cart-flow`: client-side cart with localStorage + server-side order creation
- `whatsapp-integration`: format order as WhatsApp message, return wa.me URL
- `admin-auth`: password login + signed cookie session

### Modified Capabilities
- `app-skeleton` (in `change-001-foundation`): no modification needed — `public` and `admin` routers are already in place; this change just adds routes to them
- `db-schema` (in `change-002-db-seed`): no schema change — `ordenes` and `clientes` tables already support what we need

## Approach

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CSS strategy | Component CSS file (`components.css`) added after `main.css` | Keeps tokens + main as foundation; components layered on top |
| Cart state | localStorage in browser, submitted with form | No session required; survives page refresh; simple |
| Form validation | Pydantic models in `app/schemas.py` | FastAPI native; type-safe; auto-generates OpenAPI docs |
| WhatsApp integration | Server formats message, returns `wa.me/{phone}?text={urlencoded_message}` | wa.me URLs work on mobile and desktop; no API key needed |
| Admin auth | Signed cookie with `itsdangerous` (already a FastAPI dep) + password check | Simple, no DB table needed for sessions; cookie is signed so tamper-resistant |
| Image strategy | Use `/static/img/placeholder-{sku}.svg` with simple SVG placeholders (gradient + text) | No real images yet; placeholders show product name + price |
| Starburst design | CSS-only starburst (rotated text + clip-path) | No image asset; scalable; matches the comic-book reference |
| Cart icon | CSS-only SVG inline in header | No external icon font |
| Mobile-first | Flex/grid with media queries at 640px, 960px breakpoints | Mobile is the primary use case for street food orders |
| Animations | CSS transitions only (no JS animation library) | Keep it light; MVP doesn't need framer-motion |
| Admin auth on routes | FastAPI `Depends(get_current_admin)` dependency | DRY; one place to enforce auth |

## Affected Areas

| Area | Impact |
|------|--------|
| `app/static/css/components.css` | New — ~200 LOC of component styles |
| `app/schemas.py` | New — Pydantic models for forms |
| `app/auth.py` | New — admin password check + signed cookie helpers (in `change-004-admin-ui`) |
| `app/routes/public.py` | Modified — add 3 routes |
| `app/routes/admin.py` | Modified — add 7 routes (in `change-004-admin-ui`) |
| `app/templates/public/` | New directory — 3-4 page templates (home, cart, order-confirmed) |
| `app/templates/admin/` | New directory — 4-5 page templates (login, dashboard, inventario, banner, ordenes) |
| `app/static/img/` | New — placeholder SVG files for products |
| `pyproject.toml` | Add dep: `itsdangerous` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Public UI PR is still over 400 LOC even after split | Medium | If forecast > 400, split `change-003-public-ui` further (e.g., separate cart/checkout from menu grid) |
| Admin auth via plain text password + signed cookie | Low for MVP | Acceptable for single-admin local app; document the trade-off; recommend bcrypt + user table for production |
| localStorage cart lost if user clears browser data | Low | Document in UI ("Tu carrito se guarda en este navegador"); acceptable for MVP |
| Pydantic v1 vs v2 syntax | Low | FastAPI 0.110+ uses Pydantic v2; use v2 syntax (e.g., `model_dump()` not `dict()`) |
| WhatsApp message formatting breaks if products have special chars | Low | URL-encode the message; test with quotes/newlines in product names |
| Mobile responsiveness for complex menu grid | Medium | Use CSS grid with `auto-fit, minmax(...)` for natural wrapping |
| Starburst CSS doesn't render in older browsers | Low | Acceptable; modern browsers only for MVP |

## Rollback Plan

Revert the merge commit on `main` for `change-003-public-ui` or `change-004-admin-ui`. The app returns to the foundation state. No data loss because the schema is unchanged.

## Dependencies

- `itsdangerous` (for signed cookies) — add to `pyproject.toml` runtime deps
- `pydantic` — already transitive from `fastapi`
- Modern browser with CSS Grid + `clip-path` + `backdrop-filter` support

## Success Criteria

- [ ] `change-003-public-ui` lands with all public UI working
- [ ] `change-004-admin-ui` lands with all admin UI working
- [ ] A user can: visit `/`, see the banner, browse the menu, add items to cart, fill the form, confirm the order, get redirected to WhatsApp
- [ ] The order is saved in `ordenes` and `clientes` tables
- [ ] An admin can: visit `/admin/login`, log in with `wero123`, toggle Sold Out for a SKU, update the banner text, see the new order in the orders table
- [ ] The UI is responsive (works on mobile widths 320-414px and desktop 1024px+)
- [ ] The Mexican urban identity is clearly visible (Royal Blue background, Magenta CTAs, Yellow prices, Bold display fonts)
- [ ] `mypy app/` is clean
- [ ] `ruff check app/` is clean

## Cross-references

- Companion: `change-001-foundation/` (lands first)
- Companion: `change-002-db-seed/` (lands first)
- Future: `change-005-...` for follow-ups (real images, payment, accounts)
