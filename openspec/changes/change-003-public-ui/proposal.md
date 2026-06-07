# Change 003 — Public UI

> First sub-change of the umbrella `change-002-features` (see `../change-002-features/proposal.md` for the full scope and the 2-way split).

## Intent

Brings the public-facing side of "Jochos El Perro Wero" to life. Adds the home page with the dynamic promo banner, location/hours, interactive menu grid (jochos + hamburguesas with Sold Out handling), shopping cart with customer data form, WhatsApp checkout integration, and the floating social media buttons. Also adds the component CSS layer that establishes the Mexican urban visual identity (Azul Rey + Magenta + Amarillo comic-book vibe).

This change is the **first half** of the UI work. The admin panel lands in the follow-up `change-004-admin-ui` (password login, inventory toggles, banner editor, orders viewer).

## Scope (this change only)

### In
- `app/static/css/components.css` — reusable component styles (buttons, cards, hero, footer, forms, modal, starburst)
- `app/static/img/placeholder-*.svg` — generated SVG placeholders for the 6 products
- `app/schemas.py` — Pydantic models: `CartItem`, `CustomerData`, `OrderCreate`, `OrderResponse`
- `app/routes/public.py` (modified) — `GET /`, `POST /ordenes`, `GET /ordenes/{numero_orden}/whatsapp`
- `app/templates/public/` (new) — `home.html`, `order_pending.html`
- `app/templates/public/partials/` (new) — `product_card.html`, `cart_summary.html`
- `app/static/js/cart.js` — vanilla JS cart logic backed by localStorage
- `app/static/js/order.js` — fetch POST /ordenes, redirect to WhatsApp
- `app/static/img/wero-mascot.svg` — simple SVG version of the "Wero" dog mascot
- `pyproject.toml` — add `itsdangerous` dep (for admin session, also used to sign cart data)
- Seed update: add 6 placeholder images in `app/static/img/`

### Out (deferred to `change-004-admin-ui`)
- Admin login, inventory panel, banner editor, orders viewer
- Real product images (placeholders only)
- Image upload
- Pydantic models for admin forms (`AdminLogin`, `BannerUpdate`) — those live in change-004

## Approach

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Component CSS | New file `components.css` loaded after `main.css` | Keeps tokens + main as foundation; components layered on top |
| Cart state | `localStorage` in browser, submitted with the order | No session required; survives page refresh; simple |
| Form validation | Pydantic v2 models in `app/schemas.py` | FastAPI native; type-safe; auto-generates OpenAPI docs |
| WhatsApp integration | Server formats the message and returns a `wa.me/{phone}?text={urlencoded}` URL | wa.me URLs work on mobile and desktop; no API key needed |
| Mascot | Hand-crafted SVG (yellow dog, magenta mohawk, black sunglasses, spiked collar) | No external image; small; matches the reference ads |
| Starburst design | CSS-only (rotated text + clip-path on a pseudo-element) | No image asset; scalable; matches the comic-book reference |
| Placeholder product images | Simple SVG with gradient + product name + price badge | No real images yet; recognizable as a placeholder |
| Cart icon | Inline SVG in the header | No external icon font |
| Mobile-first | CSS grid with `auto-fit, minmax(280px, 1fr)` and media queries at 640px, 960px | Mobile is the primary use case for street food orders |
| Order numbering | `ORD-{YYYYMMDD}-{6 hex chars from secrets.token_hex(3)}` | Human-readable date + short unique id |
| Customer on repeat visit | Server upserts `clientes` by `telefono` (matching unique phone) | Avoids creating duplicate client rows for repeat customers |

## Capabilities

### New Capabilities
- `public-ui`: home page, product grid, customer form, order creation route, WhatsApp redirect route
- `component-css`: reusable CSS components (buttons, cards, hero, footer, forms, modal, starburst, mascot)
- `cart-flow`: client-side cart with localStorage, server-side order persistence, order numbering
- `whatsapp-integration`: order-to-message formatter, wa.me URL builder

### Modified Capabilities
- None — all foundation specs remain untouched

## Affected Areas

| Area | Impact |
|------|--------|
| `app/static/css/components.css` | New — ~200 LOC |
| `app/static/js/cart.js` | New — ~80 LOC |
| `app/static/js/order.js` | New — ~60 LOC |
| `app/static/img/` | 6 product placeholders + 1 mascot SVG |
| `app/schemas.py` | New — ~50 LOC Pydantic models |
| `app/routes/public.py` | Modified — +3 routes (~80 LOC) |
| `app/templates/public/` | New — 2-3 page templates + 2 partials (~150 LOC Jinja) |
| `app/templates/base.html` | Modified — add `<link>` to `components.css` (1 line) |
| `pyproject.toml` | Add `itsdangerous` to runtime deps |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Total LOC exceeds 400 budget | Medium | Forecast is ~450-550; if apply trends >500, split out cart/whatsapp from public-ui |
| localStorage cart lost if user clears browser data | Low | Display note in UI ("Tu carrito se guarda en este navegador"); acceptable for MVP |
| Pydantic v2 syntax differences | Low | FastAPI 0.110+ uses Pydantic v2; use v2 syntax (`model_dump`, not `dict`) |
| WhatsApp message formatting breaks with special chars | Low | URL-encode the message; test with quotes, newlines, em-dashes |
| Mobile responsiveness for complex menu grid | Medium | CSS grid `auto-fit minmax` + tested at 320px, 414px, 1024px |
| `itsdangerous` for signing adds dep weight | Very low | Standard library for FastAPI cookies; already indirect dep |
| Customer upsert by phone collides with existing data | Low | Use `INSERT ... ON CONFLICT(telefono) DO UPDATE` or check-then-insert |

## Rollback Plan

Revert the merge commit on `main`. The app returns to the foundation state (no public UI). No data loss because the schema is unchanged.

## Dependencies

- `itsdangerous` (new) — used by change-004 for admin session, but listed here for forward compatibility
- Pydantic v2 (already transitive from FastAPI)
- Modern browser with CSS Grid + `clip-path` + `localStorage` support

## Success Criteria

- [ ] `GET /` returns 200 with the home page rendered (banner + location + menu + footer)
- [ ] The menu shows the 6 seed products loaded from the DB
- [ ] A product with `disponible=0` shows a "Agotado" badge and a disabled "Añadir" button
- [ ] Adding products to the cart persists across page reloads
- [ ] Submitting the cart form with valid data creates a `clientes` row and N `ordenes` rows
- [ ] The response is a `wa.me/...` URL with the order summary URL-encoded in the `text` query param
- [ ] The visual identity is clearly Mexican urban: Royal Blue background, Magenta CTAs, Yellow prices/starbursts, Bebas Neue / Anton display fonts
- [ ] The home page is usable at 320px width (iPhone SE) and 1024px+ (desktop)
- [ ] `mypy app/` is clean
- [ ] `ruff check app/` is clean

## Cross-references

- **Umbrella proposal**: `../change-002-features/proposal.md` (full UI scope + the 2-way split)
- **Foundation specs**: `../../specs/app-skeleton/spec.md`, `../../specs/base-templates/spec.md`, `../../specs/design-tokens/spec.md`, `../../specs/db-schema/spec.md`
- **Foundation archives**: `../archive/2026-06-07-change-001-foundation/`, `../archive/2026-06-07-change-002-db-seed/`
- **Companion change** (lands second): `../change-004-admin-ui/` (planned)
