# Tasks: Change 004 — Cart & WhatsApp Checkout

> Second sub-change of the umbrella `change-002-features`. Lands after `change-003-public-ui` and before `change-005-admin-ui`. ~275 LOC total (under 400 budget).

## Task Dependency Graph

```
T1 (schemas) → T2 (POST /ordenes) → T7 (smoke)
              → T3 (GET /whatsapp) → T7
T4 (server helpers: format_order_message, build_whatsapp_url)
              → T2, T3
T5 (order.js) → T2
T6 (order_pending.html + cart_summary.html update) → T5
```

T1 is the foundation. T4 (helpers) can be developed in parallel with T1 but is needed by T2/T3. T2 + T3 are independent of each other (both depend on T1 and T4). T5 + T6 are the frontend wiring.

## T1: Pydantic v2 Schemas
**Files**: `app/schemas.py` (new)
**Depends on**: none
**Lines estimate**: ~70
**Acceptance**:
- `app/schemas.py` defines `CartItem`, `CustomerData`, `OrderCreate`, `OrderResponse`
- Uses Pydantic v2 syntax (`Field(..., min_length=...)`, `pattern=r"..."`, `Literal["M", "F", "Otro"]`)
- `python -c "from app.schemas import OrderCreate, OrderResponse; print('OK')"` succeeds
- A valid payload parses without error; an invalid payload raises `ValidationError`

## T2: POST /ordenes Route
**Files**: `app/routes/public.py` (modified — add `create_order` function)
**Depends on**: T1, T4
**Lines estimate**: ~100
**Acceptance**:
- `POST /ordenes` accepts JSON `OrderCreate` body
- Verifies all SKUs exist (returns 404 if any missing)
- Upserts cliente by phone using `ON CONFLICT(telefono) DO UPDATE`
- Generates `numero_orden` in format `ORD-{YYYYMMDD}-{6 hex}`
- Inserts N ordenes rows in a single transaction
- Returns `OrderResponse` JSON with `whatsapp_url`
- `curl -X POST /ordenes` with valid payload returns 200; with invalid returns 422; with non-existent SKU returns 404
- `mypy app/routes/public.py` is clean

## T3: GET /ordenes/{numero_orden}/whatsapp Route
**Files**: `app/routes/public.py` (modified — add `whatsapp_redirect` function)
**Depends on**: T1, T4
**Lines estimate**: ~30
**Acceptance**:
- `GET /ordenes/{numero_orden}/whatsapp` looks up the order and returns HTTP 302
- The `Location` header is `https://wa.me/{phone}?text={urlencoded_message}`
- 404 if `numero_orden` doesn't exist
- `curl -i` shows the 302 with the correct `Location`

## T4: Server-Side Helpers
**Files**: `app/routes/public.py` (modified — add `format_order_message` and `build_whatsapp_url`)
**Depends on**: none (pure functions)
**Lines estimate**: ~50
**Acceptance**:
- `format_order_message(numero_orden, nombre, telefono, items, price_map, total) -> str` returns the Spanish message
- The message contains: header with brand + order number, customer block, items list, total, closing line in MX-ES
- `build_whatsapp_url(phone, message) -> str` returns `https://wa.me/{phone}?text={urlencoded}`
- Special chars (em-dash, ñ, $, emoji, newline, slash) are URL-encoded
- `python -c "from app.routes.public import format_order_message, build_whatsapp_url; ..."` smoke check succeeds

## T5: order.js Form Handler
**Files**: `app/static/js/order.js` (new)
**Depends on**: T1 (schemas), T2 (POST /ordenes endpoint)
**Lines estimate**: ~60
**Acceptance**:
- On `DOMContentLoaded`, hooks the `#order-form` submit event
- Reads `WeroCart.items()` and form data via `FormData`
- POSTs to `/ordenes` with JSON body
- On 200: clears cart and follows `data.whatsapp_url`
- On non-200: alerts with the error and does NOT clear the cart
- Empty cart shows an alert and does not submit
- `python3 -c "import esprima" 2>/dev/null; node -c app/static/js/order.js` syntax check (if node available)

## T6: order_pending.html + cart_summary.html Update
**Files**: `app/templates/public/order_pending.html` (new), `app/templates/public/partials/cart_summary.html` (modified)
**Depends on**: none (templates, no logic)
**Lines estimate**: ~45
**Acceptance**:
- `order_pending.html` extends `base.html`, shows the order number in the display font, the thank-you message in MX-ES, and links to `/ordenes/{numero_orden}/whatsapp` and `/`
- `cart_summary.html` (from change-003) is modified to add the `<form id="order-form">` with 4 inputs (nombre, telefono, edad, genero) and a "Confirmar pedido" submit button
- Both templates render without Jinja2 errors
- `python -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('app/templates')); e.get_template('public/order_pending.html'); e.get_template('public/partials/cart_summary.html'); print('OK')"` succeeds

## T7: Smoke Test
**Files**: (no new files; manual verification)
**Depends on**: T1, T2, T3, T4, T5, T6
**Lines estimate**: 0
**Acceptance**:
- `uvicorn app.main:app --reload` starts clean
- `curl -i http://127.0.0.1:8000/` returns 200 (home page from change-003)
- `POST /ordenes` with valid payload returns 200 with `OrderResponse`
- `POST /ordenes` with empty items returns 422
- `POST /ordenes` with non-existent SKU returns 404
- `GET /ordenes/{valid_id}/whatsapp` returns 302 with correct `Location`
- `GET /ordenes/DOES-NOT-EXIST/whatsapp` returns 404
- DB row counts increment correctly after a successful POST
- `mypy app/` is clean
- `ruff check app/` is clean
- `order_pending.html` renders with a valid order number (via Jinja2 directly)

## Total Estimate

| Task | LOC |
|------|-----|
| T1   | 70  |
| T2   | 100 |
| T3   | 30  |
| T4   | 50  |
| T5   | 60  |
| T6   | 45  |
| T7   | 0   |
| **TOTAL** | **~355** |

> Note: design.md forecast was 275 LOC; tasks estimate is 355 due to detailed helper code, schema imports, and per-task overhead in `app/routes/public.py`. Still under 400 budget.

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | **~355** |
| Budget | 400 |
| Over budget? | **No — under by ~45 lines** |
| Risk | Low — no auth, no DB schema change, well-bounded scope |
| Recommendation | **Single PR, no `size:exception` needed** |

## Commit Strategy (work-unit commits for this change)

- Commit 1: T1 (schemas) — adds `app/schemas.py` only
- Commit 2: T4 (helpers) — adds `format_order_message` + `build_whatsapp_url` to `app/routes/public.py`
- Commit 3: T2 (POST /ordenes) — adds the create_order route handler
- Commit 4: T3 (GET /whatsapp) — adds the whatsapp_redirect route handler
- Commit 5: T5 (order.js) — adds the form submit handler
- Commit 6: T6 (order_pending.html + cart_summary.html update) — adds the pending page and the form fields
- Commit 7: T7 (smoke test verification only) — updates tasks.md to mark all done

Each commit is independently revertable. After commits 1-4, the server-side flow works (testable with curl). After commit 5, the browser flow is wired. After commit 6, the pending page is reachable.

## PR Position in the Stacked-to-Main Chain

```
PR #1: change-001-foundation        (merged)
PR #2: change-002-db-seed           (in umbrella archive)
PR #3: change-003-public-ui         (lands next)
PR #4: change-004-cart-whatsapp     (THIS CHANGE — lands after #3)
PR #5: change-005-admin-ui          (planned, lands last)
```

This change lands after `change-003-public-ui` (PR #3) because it imports `WeroCart` from `app/static/js/cart.js` (added in change-003) and the cart modal UI from `app/templates/public/partials/cart_summary.html` (created in change-003, modified in T6).

## Cross-references

- **Spec**: `specs/{order-checkout,whatsapp-message}/spec.md`
- **Design**: `design.md`
- **Proposal**: `proposal.md`
- **Previous change**: `../change-003-public-ui/`
- **Companion change** (lands last): `../change-005-admin-ui/`
