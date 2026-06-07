# Verify Report: change-004-cart-whatsapp

**Date**: 2026-06-07
**Branch**: change-004-cart-whatsapp
**Verdict**: PASS

## Summary
All 7 implementation tasks complete. All 15 smoke tests pass (14 directly, 1 with noted pre-existing issue). Spec compliance matrix is fully green. `ruff check app/` is clean. New code passes mypy; the 2 mypy errors in `home` are pre-existing from change-003 and excluded from scope. One design deviation (UNIQUE on `telefono`) was correctly applied.

## Branch State
- Total commits on branch: 43
- Implementation commits (change-004): 7 (schemas → helpers → POST → GET → order.js → templates → docs)
- Under 400-line budget: **Yes** (~295 LOC)

## File Inventory
| File | Lines | Status |
|------|-------|--------|
| app/schemas.py | 26 | ✅ |
| app/routes/public.py | 158 | ✅ |
| app/static/js/order.js | 36 | ✅ |
| app/templates/public/order_pending.html | 12 | ✅ |
| app/templates/public/partials/cart_summary.html | 65 | ✅ |
| app/db.py (UNIQUE constraint) | 32 (telefono line) | ✅ |

## Smoke Test Results (15 tests)
| # | Check | Result |
|---|-------|--------|
| 1 | Valid POST /ordenes returns 200 | ✅ |
| 2 | DB has 2 ordenes rows + 2 clientes | ✅ |
| 3 | Order number format matches regex | ✅ |
| 4 | Total = 240 for 2x JO-001 + 1x HB-002 | ✅ |
| 5 | WhatsApp URL starts with wa.me/525555555555 | ✅ |
| 6 | Customer name trimmed (no leading/trailing whitespace) | ✅ |
| 7 | Empty items returns 422 | ✅ |
| 8 | Invalid phone returns 422 | ✅ |
| 9 | Non-existent SKU returns 404 | ✅ |
| 10 | Atomicity (no cliente row after 404) | ✅ |
| 11 | WhatsApp redirect returns 302 | ✅ |
| 12 | Order not found returns 404 | ✅ |
| 13 | order_pending.html renders | ✅ |
| 14 | cart_summary.html has the form | ✅ |
| 15 | Home page still works | ✅ |

## Spec Compliance
### order-checkout
- ✅ Pydantic v2 schemas: `CartItem`, `CustomerData`, `OrderCreate`, `OrderResponse` correctly defined
- ✅ POST /ordenes with valid payload returns 200 with `OrderResponse` (numero_orden, total, whatsapp_url, customer_name)
- ✅ POST /ordenes with empty items returns 422
- ✅ POST /ordenes with invalid phone returns 422
- ✅ POST /ordenes with non-existent SKU returns 404 (atomic — no rows written)
- ✅ Customer upsert by phone (no duplicate rows for same telefono)
- ✅ numero_orden format `ORD-{YYYYMMDD}-{6 hex}`
- ✅ GET /ordenes/{id}/whatsapp returns 302 with Location header
- ✅ GET /ordenes/DOES-NOT-EXIST/whatsapp returns 404
- ✅ order_pending.html renders with order number and customer name
- ✅ cart_summary.html has `<form id="order-form">` with all 4 inputs (nombre, telefono, edad, genero) and "Confirmar pedido" button

### whatsapp-message
- ✅ `format_order_message` produces Spanish message with brand, order #, customer, items, total, closing line
- ✅ `build_whatsapp_url` produces `https://wa.me/{phone}?text={urlencoded}`
- ✅ Special chars (em-dash, ñ, $, emoji, newline, slash) are URL-encoded
- ✅ Phone comes from `configuracion.whatsapp_numero` (falls back to `525555555555`)
- ✅ Message format matches spec exactly (🐶 *Jochos El Perro Wero* — Pedido {numero_orden} header, customer block, item lines, total, closing line)

## Deviations from Design
- **db.py: added `UNIQUE` constraint to `telefono`**: Required for `ON CONFLICT(telefono)` upsert. The foundation schema lacked this constraint. Without it, SQLite would allow duplicate phones and the upsert would silently insert rather than update on conflict. This is a correct and necessary deviation.
- **T2/T3/T4 consolidated into a single commit** (`08daec8 feat(api): add format_order_message and build_whatsapp_url helpers`): Helpers are in the same file as the routes, so the commits were merged for clarity. This is a practical consolidation, not a deviation from behavior.
- **Pre-existing change-003 home page bug fixed in follow-up commit** (`6b6cd56 fix(routes): correct TemplateResponse signature in home function`): The `home` function used the old Starlette `TemplateResponse(name, context)` signature with `request` inside the context dict. Newer Starlette versions break on this (Jinja2 cache key is unhashable when context contains a `request`). Fixed by switching to `TemplateResponse(request, name, context)`. Side benefit: resolves 2 pre-existing mypy errors.

## Warnings
None (home page bug fixed; all 15 smoke tests pass; ruff + mypy clean)

## Verdict
**PASS** — All 15 smoke tests pass. All spec scenarios are covered. All 7 tasks are marked complete. `ruff check app/` is clean. `mypy app/` is clean. Two design deviations (UNIQUE constraint + follow-up fix) were correctly applied and documented. The branch is ready for archive and PR.