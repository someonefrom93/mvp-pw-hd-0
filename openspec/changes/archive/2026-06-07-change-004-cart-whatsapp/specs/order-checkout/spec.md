# Capability: order-checkout

## Purpose
The end-to-end order flow: server-side Pydantic v2 validation, atomic SQLite transaction (cliente upsert by phone + N ordenes inserts in one commit), order number generation, the `POST /ordenes` route, the `GET /ordenes/{id}/whatsapp` redirect, the `order.js` form submit handler, the `order_pending.html` "thank you" page, and the customer form fields in `cart_summary.html`.

## Requirements

### Requirement: Pydantic v2 schemas
The system MUST provide `app/schemas.py` with these models:

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

#### Scenario: CartItem accepts valid input
- **GIVEN** the JSON body `{"sku": "JO-001", "cantidad": 2}`
- **WHEN** parsed as `CartItem`
- **THEN** it succeeds (sku matches pattern, cantidad between 1 and 20)

#### Scenario: CartItem rejects negative quantity
- **GIVEN** the JSON body `{"sku": "JO-001", "cantidad": 0}`
- **WHEN** parsed as `CartItem`
- **THEN** Pydantic raises `ValidationError` with message "Input should be greater than or equal to 1"

#### Scenario: CustomerData validates phone format
- **GIVEN** the JSON body `{"nombre": "Test", "telefono": "abc123", "edad": 30, "genero": "M"}`
- **WHEN** parsed as `CustomerData`
- **THEN** Pydantic raises `ValidationError` with message "String should match pattern '^\\d{10,15}$'"

#### Scenario: OrderCreate requires at least 1 item
- **GIVEN** the JSON body `{"items": [], "customer": {...}}`
- **WHEN** parsed as `OrderCreate`
- **THEN** Pydantic raises `ValidationError` with message "List should have at least 1 item"

#### Scenario: OrderResponse shape
- **GIVEN** a successful order creation
- **WHEN** the response is returned
- **THEN** the JSON has all 4 fields: `numero_orden` (str), `total` (float, positive), `whatsapp_url` (str, starts with `https://wa.me/`), `customer_name` (str)

### Requirement: POST /ordenes route
The system MUST expose `POST /ordenes` that:
1. Accepts a JSON body matching `OrderCreate`
2. Returns 422 on Pydantic validation failure
3. In a single sqlite3 transaction:
   a. Verifies all `sku` values exist in `productos` (returns 404 if any missing)
   b. Upserts the `clientes` row by `telefono` (`INSERT ... ON CONFLICT(telefono) DO UPDATE SET nombre=excluded.nombre, edad=excluded.edad, genero=excluded.genero`)
   c. Generates `numero_orden = f"ORD-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(3)}"`
   d. Inserts one `ordenes` row per cart item with `cliente_id` from step b
4. Commits the transaction
5. Reads `whatsapp_numero` from `configuracion`
6. Returns `OrderResponse` JSON with the formatted `whatsapp_url`

#### Scenario: successful order creation
- **GIVEN** the request body `{"items": [{"sku": "JO-001", "cantidad": 2}, {"sku": "HB-002", "cantidad": 1}], "customer": {"nombre": "Juan Pérez", "telefono": "5551234567", "edad": 28, "genero": "M"}}`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 200 with body `{"numero_orden": "ORD-20260607-abc123", "total": 240.0, "whatsapp_url": "https://wa.me/525555555555?text=...", "customer_name": "Juan Pérez"}`
- **AND** the DB has 1 new row in `clientes` (with telefono "5551234567") and 2 new rows in `ordenes`

#### Scenario: invalid customer data returns 422
- **GIVEN** the request body has `edad: -5`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 422 with Pydantic validation error body

#### Scenario: empty cart returns 422
- **GIVEN** the request body has `"items": []`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 422

#### Scenario: non-existent SKU returns 404
- **GIVEN** the request body has `sku: "FAKE-001"` which doesn't exist in `productos`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 404 with body `{"detail": "Uno o más productos no existen"}`
- **AND** NO rows are added to `clientes` or `ordenes` (transaction rolled back)

#### Scenario: order is atomic
- **GIVEN** the request body has 2 items, but the second SKU doesn't exist
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 404
- **AND** `SELECT COUNT(*) FROM clientes WHERE telefono='5551234567'` is 0 (no cliente was inserted)
- **AND** `SELECT COUNT(*) FROM ordenes` is unchanged

#### Scenario: total is computed correctly
- **GIVEN** a request with JO-001 (precio=65) x2 and HB-002 (precio=110) x1
- **WHEN** `POST /ordenes` is called
- **THEN** the response's `total` field is `240.0` (65*2 + 110*1)

#### Scenario: customer name is trimmed
- **GIVEN** the request body has `nombre: "  Juan Pérez  "` (whitespace)
- **WHEN** `POST /ordenes` is called
- **THEN** the cliente row's `nombre` is stored as "Juan Pérez" (no leading/trailing whitespace)

### Requirement: order number generation
The system MUST generate `numero_orden` in the format `ORD-YYYYMMDD-{6 hex chars}` where the hex chars come from `secrets.token_hex(3)`. The number is generated server-side at order creation time.

#### Scenario: numero_orden format
- **GIVEN** today is 2026-06-07
- **WHEN** an order is created
- **THEN** `numero_orden` matches the regex `^ORD-20260607-[0-9a-f]{6}$` (example: `ORD-20260607-a3f9b2`)

#### Scenario: numero_orden is unique
- **GIVEN** 1000 orders are created in the same day
- **WHEN** any two `numero_orden` values are compared
- **THEN** they are all distinct (collision probability is ~1/16M)

### Requirement: customer upsert by phone
The system MUST upsert the `clientes` row by `telefono` (the natural unique key for street-food customers). The SQL MUST be:
```sql
INSERT INTO clientes (nombre, telefono, edad, genero) VALUES (?, ?, ?, ?)
ON CONFLICT(telefono) DO UPDATE SET
  nombre = excluded.nombre,
  edad = excluded.edad,
  genero = excluded.genero
```

#### Scenario: new customer
- **GIVEN** no client exists with telefono "5551234567"
- **WHEN** an order is created with that phone
- **THEN** after the request, `SELECT COUNT(*) FROM clientes WHERE telefono='5551234567'` is 1
- **AND** the new cliente's `nombre`, `edad`, `genero` match the request

#### Scenario: repeat customer upserts
- **GIVEN** a client exists with telefono "5551234567" (nombre "Juan", edad 28)
- **WHEN** an order is created with telefono "5551234567", nombre "Juan Pérez", edad 29
- **THEN** the cliente row is updated to (nombre="Juan Pérez", edad=29, genero="M")
- **AND** only 1 cliente row exists with telefono "5551234567" (no duplicate)

### Requirement: order persistence
The system MUST persist each `POST /ordenes` request as:
- 1 row in `clientes` (via the upsert above)
- N rows in `ordenes` (one per cart item)
- All in a SINGLE sqlite3 transaction (commit at the end, rollback on any error)

#### Scenario: order lines have correct columns
- **GIVEN** an order is created for 2x JO-001 (precio=65) and 1x HB-002 (precio=110)
- **WHEN** the order is persisted
- **THEN** the `ordenes` table has 2 rows with: (numero_orden, cliente_id, sku="JO-001", producto="Jocho Clásico", precio=65.0, cantidad=2) and (numero_orden, cliente_id, sku="HB-002", producto="Hamburguesa con Tocino", precio=110.0, cantidad=1)

### Requirement: GET /ordenes/{numero_orden}/whatsapp redirect
The system MUST expose `GET /ordenes/{numero_orden}/whatsapp` that:
1. Looks up all `ordenes` rows with that `numero_orden`
2. If none, returns HTTP 404
3. Looks up the `cliente` (nombre, telefono) via `cliente_id`
4. Looks up the WhatsApp phone from `configuracion.whatsapp_numero`
5. Calls `format_order_message(...)` to build the message text
6. Returns HTTP 302 with `Location: https://wa.me/{phone}?text={quote(message, safe='')}`

#### Scenario: successful redirect
- **GIVEN** order "ORD-20260607-abc123" exists with customer "Juan Pérez" and 2 items
- **WHEN** `GET /ordenes/ORD-20260607-abc123/whatsapp` is called
- **THEN** the response is HTTP 302
- **AND** the `Location` header is `https://wa.me/525555555555?text=...` containing the formatted message

#### Scenario: order not found returns 404
- **GIVEN** no order with numero_orden "ORD-DOES-NOT-EXIST"
- **WHEN** `GET /ordenes/ORD-DOES-NOT-EXIST/whatsapp` is called
- **THEN** the response is HTTP 404 with body `{"detail": "Order not found"}`

#### Scenario: redirect URL is wa.me
- **GIVEN** any existing order
- **WHEN** the redirect is followed
- **THEN** the URL starts with `https://wa.me/` (not api.whatsapp.com or web.whatsapp.com)

### Requirement: order_pending.html page
The system MUST provide `app/templates/public/order_pending.html` that extends `base.html` and:
- Shows the `numero_orden` prominently in the display font with Magenta background
- Shows "¡Gracias por tu pedido, {customer_name}!" in Spanish
- Has a "Continuar a WhatsApp" link pointing to `/ordenes/{numero_orden}/whatsapp`
- Includes the Wero mascot SVG for branding

#### Scenario: pending page renders
- **GIVEN** the page is rendered with `{"numero_orden": "ORD-20260607-abc123", "customer_name": "Juan"}`
- **WHEN** the HTML is inspected
- **THEN** it contains the order number, the thank-you message in Spanish, and the link to the WhatsApp redirect

#### Scenario: pending page has back link
- **GIVEN** the pending page is rendered
- **WHEN** the user clicks "Volver al inicio"
- **THEN** they are taken to `GET /`

### Requirement: cart_summary.html with customer form
The system MUST modify `app/templates/public/partials/cart_summary.html` (created in `change-003-public-ui`) to add:
- An `<form id="order-form">` containing the customer fields
- 4 inputs: `nombre` (text, required, min 2), `telefono` (text, required, pattern), `edad` (number, required, min 1, max 120), `genero` (radio, required, M/F/Otro)
- A "Confirmar pedido" submit button (`.btn.btn-magenta.btn-block`)

#### Scenario: form has all required fields
- **GIVEN** the modified `cart_summary.html` is rendered
- **WHEN** the HTML is inspected
- **THEN** it contains `<form id="order-form">` with 4 inputs (nombre, telefono, edad, genero) and a submit button

#### Scenario: form validation is client-side
- **GIVEN** the user clicks "Confirmar pedido" with an empty telefono field
- **WHEN** the form submits
- **THEN** the browser shows a native validation message ("Please fill out this field")

### Requirement: order.js form handler
The system MUST provide `app/static/js/order.js` that:
- On `DOMContentLoaded`, hooks the `#order-form` submit event
- Prevents default form submit
- Reads `WeroCart.items()`; if empty, alerts and returns
- Reads form data via `FormData(form)`
- Builds an `OrderCreate` JSON payload
- `fetch('POST /ordenes', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)})`
- On 200 response: `WeroCart.clear()`, then `window.location.href = data.whatsapp_url`
- On non-200 response: shows an alert with the error message and does NOT clear the cart

#### Scenario: form submit posts cart and customer
- **GIVEN** the cart has 2 items and the customer form is filled
- **WHEN** the user clicks "Confirmar pedido"
- **THEN** a `POST /ordenes` request is sent with the correct JSON body
- **AND** the browser follows the response's `whatsapp_url`
- **AND** `localStorage.wero_cart_v1` is `{}` (cleared)

#### Scenario: empty cart shows alert
- **GIVEN** `WeroCart` is empty
- **WHEN** the user clicks "Confirmar pedido"
- **THEN** an alert "Tu carrito está vacío" appears
- **AND** NO request is sent

#### Scenario: server error preserves cart
- **GIVEN** the server returns 500 (or any non-200)
- **WHEN** the user submits the form
- **THEN** an alert with the error message appears
- **AND** `localStorage.wero_cart_v1` is NOT cleared (the user can retry)

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
