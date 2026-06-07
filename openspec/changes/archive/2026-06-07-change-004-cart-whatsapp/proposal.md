# Change 004 — Cart & WhatsApp Checkout

> Second sub-change of the umbrella `change-002-features` (see `../change-002-features/proposal.md` for the full scope and the 3-way split). Lands after `change-003-public-ui` and before `change-005-admin-ui`.

## Intent

Adds the transactional layer on top of the public UI shell from `change-003-public-ui`. Specifically: Pydantic v2 request/response schemas, the `POST /ordenes` route with atomic cliente upsert + ordenes inserts, the `GET /ordenes/{numero_orden}/whatsapp` redirect route, the `order.js` form submit handler, the `order_pending.html` "thank you" page, the customer form fields in `cart_summary.html`, and the server-side helpers for formatting the order as a Spanish WhatsApp message and building the `wa.me/...` URL.

After this change lands, a customer can: visit `/`, browse the menu, add items to the cart, fill the customer form in the cart modal, click "Confirmar pedido", and get redirected to WhatsApp with the full order summary pre-filled. The order is persisted in the DB.

## Scope (this change only)

### In
- `app/schemas.py` (NEW) — Pydantic v2 models: `CartItem`, `CustomerData`, `OrderCreate`, `OrderResponse`
- `app/routes/public.py` (modified) — `POST /ordenes` and `GET /ordenes/{numero_orden}/whatsapp` (the home page route `GET /` is from `change-003-public-ui`)
- `app/static/js/order.js` (NEW) — form submit handler: reads `WeroCart`, builds `OrderCreate` JSON, POSTs to `/ordenes`, redirects to `data.whatsapp_url`
- `app/templates/public/order_pending.html` (NEW) — "¡Gracias por tu pedido, {nombre}!" page with order number and "Continuar a WhatsApp" link
- `app/templates/public/partials/cart_summary.html` (MODIFIED) — add customer form fields (nombre, telefono, edad, genero) and the "Confirmar pedido" submit button
- Server-side helpers in `app/routes/public.py`:
  - `format_order_message(numero_orden, nombre, telefono, items, price_map, total) -> str` — formats the order as a Spanish WhatsApp message
  - `build_whatsapp_url(phone: str, message: str) -> str` — returns `https://wa.me/{phone}?text={quote(message, safe='')}`
- Order numbering: `ORD-{YYYYMMDD}-{6 hex chars from secrets.token_hex(3)}`
- Atomic transaction: cliente upsert by telefono + N ordenes inserts in a single sqlite3 transaction

### Out (deferred to `change-005-admin-ui`)
- Admin login, inventory panel, banner editor, orders viewer
- Real product images
- Image upload
- `AdminLogin`, `BannerUpdate` Pydantic models

### Out (NOT in scope of this change, lives in change-003-public-ui)
- Home page rendering
- `components.css`
- WeroCart object (vanilla JS + localStorage)
- Product card partial
- Mascot SVG, product placeholders
- Social media buttons

## Approach

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Order numbering | `ORD-{YYYYMMDD}-{secrets.token_hex(3)}` | Human-readable date + 6 hex chars; collision ~1/16M |
| Customer identity | Phone (10-15 digits, no `+` prefix); upsert on conflict | Avoids duplicate client rows; phone is a natural unique ID for street-food customers |
| Atomicity | Single sqlite3 transaction with `commit()` at end | If any INSERT fails, the cliente + ordenes are rolled back together |
| SQL upsert | `INSERT INTO clientes ... ON CONFLICT(telefono) DO UPDATE SET ...` | SQLite 3.24+ syntax; works with the stdlib `sqlite3` module |
| URL encoding | `urllib.parse.quote(message, safe='')` | wa.me expects fully URL-encoded text; no `+` for spaces |
| Body format | JSON (`Content-Type: application/json`) | Pydantic-native; no multipart parsing |
| Phone source | `configuracion.whatsapp_numero` (seed: `525555555555`) | Admin can update later (change-005-admin-ui) |
| Customer phone validation | Pydantic `pattern=r"^\d{10,15}$"` | Mexico phones are 10 digits; allow international without `+` |
| Quantity limits | `ge=1, le=20` per item, `max_length=50` per order | Reasonable upper bound for a street-food order |
| Order not found | HTTP 404 with `{"detail": "Order not found"}` | FastAPI standard error format |
| Validation errors | HTTP 422 (FastAPI default for Pydantic) | Standard; no custom handler needed |
| Order pending page | Server-rendered with the order number and customer name | Fast load; no JS needed for the thank-you page |

## Capabilities

### New Capabilities
- `order-checkout`: Pydantic schemas, `POST /ordenes` with atomic transaction, `GET /whatsapp` redirect, `order_pending.html`, `cart_summary.html` with form
- `whatsapp-message`: `format_order_message` helper, `build_whatsapp_url` helper, Spanish message format

### Modified Capabilities
- None — the foundation and `change-003-public-ui` capabilities remain untouched

## Affected Areas

| Area | Impact |
|------|--------|
| `app/schemas.py` | New — ~70 LOC Pydantic v2 models |
| `app/routes/public.py` | Modified — +2 routes (`POST /ordenes`, `GET /whatsapp`) + 2 helpers (~180 LOC) |
| `app/static/js/order.js` | New — ~60 LOC form handler |
| `app/templates/public/order_pending.html` | New — ~30 LOC |
| `app/templates/public/partials/cart_summary.html` | Modified — add form fields (~+15 LOC, was created in change-003) |
| `pyproject.toml` | No new deps (itsdangerous was added in change-003 for forward compat) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| `INSERT ... ON CONFLICT` not supported on older SQLite | Low | Requires SQLite 3.24+; modern Python ships with 3.37+ |
| Race condition on order number | Very low | `secrets.token_hex(3)` is cryptographically random; collision ~1/16M |
| Cart data in localStorage doesn't match server prices | Low | Server uses DB prices, not client-supplied prices |
| Customer form bypassed (cURL POST) | Low | Pydantic validates server-side; missing fields → 422 |
| `quote(safe='')` encodes too aggressively | Very low | Tested with em-dash, ñ, $, emoji, newline |
| `order_pending.html` accessed directly without an order | Low | Page receives `numero_orden` and `customer_name` from server; cannot be hot-linked without an order |
| Customer enters invalid phone format | Low | Pydantic pattern returns 422 with clear error |
| Whitespace in customer name | Low | `str.strip()` in the route handler before DB insert |

## Rollback Plan

Revert the merge commit on `main`. The app returns to the `change-003-public-ui` state (cart works, but no checkout). No data loss because the schema is unchanged. The new ordenes rows are deleted (or kept, harmless).

## Dependencies

- No new Python deps
- Modern browser with `fetch` API and `localStorage` (already required by change-003)
- `urllib.parse.quote` (stdlib)
- `secrets.token_hex` (stdlib)
- `datetime.date` (stdlib)

## Success Criteria

- [ ] `POST /ordenes` with valid payload returns HTTP 200 with `OrderResponse` JSON (numero_orden, total, whatsapp_url, customer_name)
- [ ] `POST /ordenes` with empty items returns HTTP 422
- [ ] `POST /ordenes` with invalid phone returns HTTP 422
- [ ] `POST /ordenes` with non-existent SKU returns HTTP 404 (no rows written — atomicity)
- [ ] The DB has 1 new `clientes` row + N new `ordenes` rows after a successful POST
- [ ] A second POST with the same `telefono` upserts the cliente (no duplicate row)
- [ ] `numero_orden` matches the regex `^ORD-\d{8}-[0-9a-f]{6}$`
- [ ] The `whatsapp_url` starts with `https://wa.me/525555555555?text=...` and the text is URL-encoded
- [ ] The message text contains the brand name, order number, customer name, all items with subtotals, total, and the closing Spanish line
- [ ] `GET /ordenes/{numero_orden}/whatsapp` returns HTTP 302 with `Location: https://wa.me/...`
- [ ] `GET /ordenes/DOES-NOT-EXIST/whatsapp` returns HTTP 404
- [ ] The `order_pending.html` page renders with the order number and customer name
- [ ] `mypy app/` is clean
- [ ] `ruff check app/` is clean

## Cross-references

- **Umbrella proposal**: `../change-002-features/proposal.md` (full UI scope + the 3-way split)
- **Previous change (UI shell)**: `../change-003-public-ui/` (lands first, provides WeroCart, home page, components.css)
- **Foundation specs**: `../../specs/{app-skeleton,base-templates,design-tokens,db-schema}/spec.md`
- **Public UI specs (end state)**: `../change-003-public-ui/specs/{public-ui,component-css,cart-flow,whatsapp-integration}/spec.md` — these describe the full end state; this change implements the server-side subset
- **Companion change** (lands last): `../change-005-admin-ui/` (planned)
