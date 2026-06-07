# Design: Change 004 — Cart & WhatsApp Checkout

## 1. Overview

The transactional layer that turns the public UI shell from `change-003-public-ui` into a working order flow. Pydantic v2 validation, atomic SQLite transaction (cliente upsert + N ordenes), `ORD-{YYYYMMDD}-{6 hex}` order numbers, server-formatted Spanish WhatsApp message, and the `wa.me/{phone}?text=...` URL that opens WhatsApp with the order pre-filled.

## 2. File Tree (this change only)

```
app/
├── schemas.py                          (NEW, ~70 LOC Pydantic v2 models)
├── routes/
│   └── public.py                       (MODIFIED, +2 routes + 2 helpers, ~180 LOC)
├── templates/
│   └── public/
│       ├── order_pending.html          (NEW, ~30 LOC)
│       └── partials/
│           └── cart_summary.html       (MODIFIED, +15 LOC customer form)
└── static/
    └── js/
        └── order.js                    (NEW, ~60 LOC form handler)
```

Total: 2 new files + 2 modified, ~275 LOC.

## 3. Module Responsibilities

| File | Responsibility | Public symbols |
|------|----------------|----------------|
| `app/schemas.py` | Pydantic v2 request/response models | `CartItem`, `CustomerData`, `OrderCreate`, `OrderResponse` |
| `app/routes/public.py` | `POST /ordenes` (create), `GET /ordenes/{id}/whatsapp` (redirect), `format_order_message`, `build_whatsapp_url` | existing `router` (extended) |
| `app/templates/public/order_pending.html` | "¡Gracias por tu pedido!" page | — |
| `app/templates/public/partials/cart_summary.html` | Cart modal with customer form (MODIFIED) | — |
| `app/static/js/order.js` | Form submit handler: POST /ordenes + redirect | — |

## 4. Pydantic Schemas (app/schemas.py)

```python
from typing import Literal
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    sku: str = Field(..., min_length=1, max_length=32)
    cantidad: int = Field(..., ge=1, le=20)


class CustomerData(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    telefono: str = Field(..., pattern=r"^\d{10,15}$")
    edad: int = Field(..., ge=1, le=120)
    genero: Literal["M", "F", "Otro"]


class OrderCreate(BaseModel):
    items: list[CartItem] = Field(..., min_length=1, max_length=50)
    customer: CustomerData


class OrderResponse(BaseModel):
    numero_orden: str
    total: float
    whatsapp_url: str
    customer_name: str
```

## 5. Route Handlers (app/routes/public.py — additions)

```python
from datetime import date
import secrets
from urllib.parse import quote

from fastapi import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.schemas import OrderCreate, OrderResponse

templates = Jinja2Templates(directory="app/templates")
WHATSAPP_PHONE_FALLBACK = "525555555555"


@router.post("/ordenes", response_model=OrderResponse)
def create_order(payload: OrderCreate) -> OrderResponse:
    nombre = payload.customer.nombre.strip()
    with get_db() as conn:
        cur = conn.cursor()
        # 1. Verify all SKUs exist
        skus = [item.sku for item in payload.items]
        placeholders = ",".join("?" * len(skus))
        found = cur.execute(
            f"SELECT sku, nombre, precio FROM productos WHERE sku IN ({placeholders})",
            skus,
        ).fetchall()
        if len(found) != len(skus):
            raise HTTPException(status_code=404, detail="Uno o más productos no existen")

        # 2. Upsert cliente by phone
        cur.execute(
            "INSERT INTO clientes (nombre, telefono, edad, genero) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(telefono) DO UPDATE SET "
            "  nombre=excluded.nombre, edad=excluded.edad, genero=excluded.genero",
            (nombre, payload.customer.telefono, payload.customer.edad, payload.customer.genero),
        )
        cliente_id = cur.execute(
            "SELECT id FROM clientes WHERE telefono = ?", (payload.customer.telefono,)
        ).fetchone()["id"]

        # 3. Generate order number
        numero_orden = f"ORD-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(3)}"

        # 4. Insert order lines + compute total
        total = 0.0
        price_map = {r["sku"]: (r["nombre"], r["precio"]) for r in found}
        for item in payload.items:
            nombre_prod, precio = price_map[item.sku]
            cur.execute(
                "INSERT INTO ordenes (numero_orden, cliente_id, sku, producto, precio, cantidad) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (numero_orden, cliente_id, item.sku, nombre_prod, precio, item.cantidad),
            )
            total += precio * item.cantidad

        # 5. Get whatsapp phone
        phone_row = cur.execute(
            "SELECT valor FROM configuracion WHERE llave = 'whatsapp_numero'"
        ).fetchone()
        phone = phone_row["valor"] if phone_row else WHATSAPP_PHONE_FALLBACK
        conn.commit()

    # 6. Build whatsapp URL
    message = format_order_message(numero_orden, nombre, payload.customer.telefono,
                                   [item.model_dump() for item in payload.items],
                                   price_map, total)
    whatsapp_url = build_whatsapp_url(phone, message)

    return OrderResponse(
        numero_orden=numero_orden,
        total=total,
        whatsapp_url=whatsapp_url,
        customer_name=nombre,
    )


@router.get("/ordenes/{numero_orden}/whatsapp")
def whatsapp_redirect(numero_orden: str) -> RedirectResponse:
    with get_db() as conn:
        order_rows = conn.execute(
            "SELECT sku, producto, precio, cantidad, cliente_id FROM ordenes WHERE numero_orden = ?",
            (numero_orden,),
        ).fetchall()
        if not order_rows:
            raise HTTPException(status_code=404, detail="Order not found")
        cliente = conn.execute(
            "SELECT nombre, telefono FROM clientes WHERE id = ?",
            (order_rows[0]["cliente_id"],),
        ).fetchone()
        phone_row = conn.execute(
            "SELECT valor FROM configuracion WHERE llave = 'whatsapp_numero'"
        ).fetchone()
    phone = phone_row["valor"] if phone_row else WHATSAPP_PHONE_FALLBACK
    items = [(r["sku"], r["producto"], r["precio"], r["cantidad"]) for r in order_rows]
    total = sum(r["precio"] * r["cantidad"] for r in order_rows)
    message = format_order_message(numero_orden, cliente["nombre"], cliente["telefono"],
                                   items, None, total)
    return RedirectResponse(url=build_whatsapp_url(phone, message), status_code=302)


def build_whatsapp_url(phone: str, message: str) -> str:
    return f"https://wa.me/{phone}?text={quote(message, safe='')}"


def format_order_message(numero_orden: str, nombre: str, telefono: str,
                         items: list, price_map: dict | None, total: float) -> str:
    lines = [
        f"🐶 *Jochos El Perro Wero* — Pedido {numero_orden}",
        "",
        f"*Cliente:* {nombre}",
        f"*Teléfono:* {telefono}",
        "",
        "*Tu pedido:*",
    ]
    for item in items:
        if isinstance(item, dict):
            sku, cantidad = item["sku"], item["cantidad"]
            nombre_prod, precio = price_map[sku]
        else:
            _, nombre_prod, precio, cantidad = item
        subtotal = precio * cantidad
        lines.append(f"• {cantidad}x {nombre_prod} — ${subtotal:.0f}")
    lines += [
        "",
        f"*Total:* ${total:.0f}",
        "",
        "¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭",
    ]
    return "\n".join(lines)
```

## 6. order.js (form submit handler)

```js
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('order-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const items = WeroCart.items();
    if (items.length === 0) { alert('Tu carrito está vacío'); return; }
    const fd = new FormData(form);
    const customer = {
      nombre: fd.get('nombre'),
      telefono: fd.get('telefono'),
      edad: parseInt(fd.get('edad'), 10),
      genero: fd.get('genero'),
    };
    const resp = await fetch('/ordenes', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({items, customer}),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({detail: 'Error desconocido'}));
      alert('Error: ' + (err.detail || resp.statusText));
      return;
    }
    const data = await resp.json();
    WeroCart.clear();
    window.location.href = data.whatsapp_url;
  });
});
```

## 7. cart_summary.html modification (added fields)

```html
<form id="order-form">
  <div class="form-row">
    <label class="form-label" for="nombre">Nombre</label>
    <input class="form-input" type="text" name="nombre" id="nombre" required minlength="2" maxlength="120">
  </div>
  <div class="form-row">
    <label class="form-label" for="telefono">Teléfono (10 dígitos)</label>
    <input class="form-input" type="tel" name="telefono" id="telefono" required pattern="\d{10,15}">
  </div>
  <div class="form-row">
    <label class="form-label" for="edad">Edad</label>
    <input class="form-input" type="number" name="edad" id="edad" required min="1" max="120">
  </div>
  <div class="form-row">
    <label class="form-label">Género</label>
    <label><input type="radio" name="genero" value="M" required> M</label>
    <label><input type="radio" name="genero" value="F"> F</label>
    <label><input type="radio" name="genero" value="Otro"> Otro</label>
  </div>
  <button type="submit" class="btn btn-magenta btn-block">Confirmar pedido</button>
</form>
```

## 8. order_pending.html

```html
{% extends "base.html" %}
{% block title %}¡Pedido confirmado! · Jochos El Perro Wero{% endblock %}
{% block content %}
<main class="container">
  <section class="order-pending">
    <img src="/static/img/wero-mascot.svg" alt="Wero" class="order-pending__mascot">
    <h1 class="order-pending__title">¡Gracias por tu pedido, {{ customer_name }}!</h1>
    <p class="order-pending__number">Número de pedido: <strong>{{ numero_orden }}</strong></p>
    <a href="/ordenes/{{ numero_orden }}/whatsapp" class="btn btn-magenta">Continuar a WhatsApp</a>
    <a href="/" class="btn btn-outline">Volver al inicio</a>
  </section>
</main>
{% endblock %}
```

## 9. Sequence — POST /ordenes

```
1. Browser clicks "Confirmar pedido" in the cart modal
2. order.js: form submit handler fires (preventDefault)
3. order.js: WeroCart.items() → [{sku, cantidad}, ...]
4. order.js: FormData(form) → {nombre, telefono, edad, genero}
5. order.js: build OrderCreate JSON
6. order.js: fetch('POST /ordenes', {body: JSON, Content-Type: application/json})
7. FastAPI: parses OrderCreate (Pydantic v2 validation)
   - If invalid → 422 (e.g., empty items, bad phone)
8. Route handler: opens DB context (get_db)
9.   8a. SELECT * FROM productos WHERE sku IN (?,?,...) — verify all SKUs
10.  8b. If count != requested → 404, transaction auto-rollback on context exit
11.  8c. INSERT ... ON CONFLICT(telefono) DO UPDATE for cliente
12.  8d. SELECT id FROM clientes WHERE telefono = ?
13.  8e. numero_orden = f"ORD-{YYYYMMDD}-{secrets.token_hex(3)}"
14.  8f. Loop: INSERT INTO ordenes (numero_orden, cliente_id, sku, producto, precio, cantidad)
15.  8g. SELECT valor FROM configuracion WHERE llave = 'whatsapp_numero'
16.  8h. conn.commit()
17. Route handler: format_order_message(numero_orden, customer, items, price_map, total)
18. Route handler: build_whatsapp_url(phone, message)
19. Route handler: return OrderResponse JSON
20. order.js: WeroCart.clear()
21. order.js: window.location.href = data.whatsapp_url
22. Browser navigates to wa.me/... (opens WhatsApp)
```

## 10. Sequence — GET /ordenes/{id}/whatsapp

```
1. Browser follows link or redirect
2. FastAPI: route handler
3. SELECT ordenes WHERE numero_orden = ?
4. If empty → 404 "Order not found"
5. SELECT clientes WHERE id = cliente_id (from order row)
6. SELECT valor FROM configuracion WHERE llave = 'whatsapp_numero'
7. format_order_message(numero_orden, nombre, telefono, [(sku, producto, precio, cantidad), ...], None, total)
8. build_whatsapp_url(phone, message)
9. Return RedirectResponse(url=wa.me/..., status_code=302)
10. Browser follows the Location header
```

## 11. Key Decisions and Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Order numbering | `ORD-{YYYYMMDD}-{secrets.token_hex(3)}` | Human-readable date + 6 hex chars; collision ~1/16M |
| Customer identity | Phone (10-15 digits, no `+` prefix); upsert on conflict | Avoids duplicate client rows; phone is a natural unique ID for street-food customers |
| Atomicity | Single sqlite3 transaction with `commit()` at end | If any INSERT fails, the cliente + ordenes are rolled back together |
| SQL upsert | `INSERT INTO clientes ... ON CONFLICT(telefono) DO UPDATE SET ...` | SQLite 3.24+ syntax; works with the stdlib `sqlite3` module |
| URL encoding | `urllib.parse.quote(message, safe='')` | wa.me expects fully URL-encoded text; no `+` for spaces |
| Body format | JSON | Pydantic-native; no multipart parsing |
| Phone source | `configuracion.whatsapp_numero` (seed: `525555555555`) | Admin can update later (change-005-admin-ui) |
| Customer phone validation | Pydantic `pattern=r"^\d{10,15}$"` | Mexico phones are 10 digits; allow international without `+` |
| Quantity limits | `ge=1, le=20` per item, `max_length=50` per order | Reasonable upper bound for a street-food order |
| Order not found | HTTP 404 with `{"detail": "Order not found"}` | FastAPI standard error format |
| Validation errors | HTTP 422 (FastAPI default) | Standard; no custom handler needed |
| Order pending page | Server-rendered with the order number and customer name | Fast load; no JS needed |
| Customer name trim | `nombre.strip()` before insert | Avoids accidental leading/trailing whitespace |
| Cart clear timing | After successful 200 response, before redirect | If the server errors, the cart is preserved for retry |

## 12. Out of Scope (deferred to change-005-admin-ui)

- Admin login screen and password validation
- Admin inventory panel (toggling `disponible` for each SKU)
- Admin banner editor (updating `configuracion.banner_promocion`)
- Admin orders viewer (dataframe of recent orders)
- Admin auth (signed cookie via itsdangerous)
- `AdminLogin` and `BannerUpdate` Pydantic models

## 13. Risks

- **LOC budget**: ~275 LOC, well under 400 — no size:exception needed
- **`INSERT ... ON CONFLICT` requires SQLite 3.24+**: modern Python ships 3.37+; verified safe
- **Race condition on order number**: `secrets.token_hex(3)` is cryptographically random; collision probability ~1/16M
- **localStorage cart doesn't match server prices**: server uses DB prices, not client-supplied prices
- **Customer form bypassed (cURL POST)**: Pydantic validates server-side; missing fields → 422
- **`quote(safe='')` encodes too aggressively**: tested with em-dash, ñ, $, emoji, newline
- **Order pending page hot-linked**: the page requires `numero_orden` and `customer_name` from server; cannot be hot-linked without an order
- **Whitespace in customer name**: stripped in the route handler

## 14. Smoke Test (for sdd-verify)

```bash
# Boot (after change-003 is merged)
uvicorn app.main:app --reload

# 1. POST /ordenes with valid payload
curl -fsS -X POST http://127.0.0.1:8000/ordenes \
  -H "Content-Type: application/json" \
  -d '{"items":[{"sku":"JO-001","cantidad":2}],"customer":{"nombre":"Test","telefono":"5551111111","edad":30,"genero":"M"}}'
# → {"numero_orden":"ORD-...","total":130.0,"whatsapp_url":"https://wa.me/525555555555?text=...","customer_name":"Test"}

# 2. DB has the order
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM ordenes;"  # → 1
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM clientes;"  # → 3 (was 2)

# 3. POST /ordenes with empty items returns 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/ordenes \
  -H "Content-Type: application/json" -d '{"items":[],"customer":{...}}'
# → 422

# 4. POST /ordenes with invalid phone returns 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/ordenes \
  -H "Content-Type: application/json" -d '{"items":[...],"customer":{"nombre":"X","telefono":"abc","edad":30,"genero":"M"}}'
# → 422

# 5. POST /ordenes with non-existent SKU returns 404
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/ordenes \
  -H "Content-Type: application/json" -d '{"items":[{"sku":"FAKE","cantidad":1}],"customer":{...}}'
# → 404

# 6. Atomicity: after 404, no new cliente row
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM clientes WHERE telefono='FAKE-customer-phone';"
# → 0

# 7. WhatsApp redirect
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" \
  http://127.0.0.1:8000/ordenes/ORD-.../whatsapp
# → 302 https://wa.me/525555555555?text=...

# 8. Order not found returns 404
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/ordenes/ORD-DOES-NOT-EXIST/whatsapp
# → 404

# 9. order_pending.html renders
curl -fsS "http://127.0.0.1:8000/ordenes/ORD-.../pending" | grep -q "¡Gracias por tu pedido"
# (assuming a /pending route is added) OR
# Just verify the template loads via Jinja2 directly
python3 -c "from jinja2 import Environment, FileSystemLoader
e = Environment(loader=FileSystemLoader('app/templates'))
t = e.get_template('public/order_pending.html')
output = t.render(numero_orden='ORD-TEST', customer_name='Test')
assert '¡Gracias por tu pedido, Test!' in output
print('OK')"
```

## 15. Dependencies

- No new Python deps
- `urllib.parse.quote` (stdlib)
- `secrets.token_hex` (stdlib)
- `datetime.date` (stdlib)
- Modern browser with `fetch` API

## Cross-references

- Proposal: `proposal.md` (this change)
- Specs: `specs/{order-checkout,whatsapp-message}/spec.md`
- Previous change (UI shell): `../change-003-public-ui/` (lands first)
- Public UI end-state specs: `../change-003-public-ui/specs/{public-ui,cart-flow,whatsapp-integration}/spec.md`
- Umbrella: `../change-002-features/proposal.md`
- Companion (lands last): `../change-005-admin-ui/` (planned)
