# Capability: cart-flow

## Purpose
The end-to-end cart flow: client-side state in `localStorage` (vanilla JS, no framework), server-side validation via Pydantic, and order persistence (one `clientes` row + N `ordenes` rows in a single transaction) with a unique `numero_orden`.

## Requirements

### Requirement: client-side cart object
The system MUST expose a global `WeroCart` object in `app/static/js/cart.js` with these methods (all sync, all returning `WeroCart` for chaining):
- `WeroCart.items()` → `Array<{sku, cantidad}>` (current items)
- `WeroCart.add(sku, cantidad=1)` → adds or increments; emits `cart:change`
- `WeroCart.remove(sku)` → removes the SKU entirely; emits `cart:change`
- `WeroCart.update(sku, cantidad)` → sets the quantity (removes if 0 or negative); emits `cart:change`
- `WeroCart.clear()` → empties the cart; emits `cart:change`
- `WeroCart.count()` → number of distinct SKUs
- `WeroCart.totalQty()` → sum of quantities
- `WeroCart.isEmpty()` → boolean

State is persisted to `localStorage` under key `wero_cart_v1` as a JSON object `{sku: cantidad}`. On `DOMContentLoaded`, the cart restores from `localStorage` and emits `cart:change` so the UI updates.

#### Scenario: add new item
- **GIVEN** `WeroCart` is empty
- **WHEN** `WeroCart.add("JO-001", 2)` is called
- **THEN** `WeroCart.items()` returns `[{sku: "JO-001", cantidad: 2}]` and `localStorage.wero_cart_v1` is `{"JO-001": 2}`

#### Scenario: add to existing item
- **GIVEN** `WeroCart` has `{"JO-001": 2}`
- **WHEN** `WeroCart.add("JO-001", 1)` is called
- **THEN** `WeroCart.items()` returns `[{sku: "JO-001", cantidad: 3}]` and `localStorage.wero_cart_v1` is `{"JO-001": 3}`

#### Scenario: remove item
- **GIVEN** `WeroCart` has `{"JO-001": 2, "HB-002": 1}`
- **WHEN** `WeroCart.remove("JO-001")` is called
- **THEN** `WeroCart.items()` returns `[{sku: "HB-002", cantidad: 1}]` and `localStorage.wero_cart_v1` is `{"HB-002": 1}`

#### Scenario: clear cart
- **GIVEN** `WeroCart` has items
- **WHEN** `WeroCart.clear()` is called
- **THEN** `WeroCart.items()` returns `[]` and `localStorage.wero_cart_v1` is `{}`

#### Scenario: cart change event
- **GIVEN** a listener is attached: `document.addEventListener("cart:change", () => updateUI())`
- **WHEN** any mutation method is called
- **THEN** the `cart:change` event fires exactly once and `updateUI()` is called

### Requirement: server-side Pydantic schemas
The system MUST provide `app/schemas.py` with these Pydantic v2 models:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

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
```

#### Scenario: CartItem validates
- **GIVEN** a request body with `{"sku": "JO-001", "cantidad": 2}`
- **WHEN** parsed as `CartItem`
- **THEN** it succeeds (cantidad is between 1 and 20)

#### Scenario: CartItem rejects negative quantity
- **GIVEN** a request body with `{"sku": "JO-001", "cantidad": 0}`
- **WHEN** parsed as `CartItem`
- **THEN** Pydantic raises ValidationError (cantidad must be >= 1)

#### Scenario: CustomerData validates phone format
- **GIVEN** a request body with `{"telefono": "abc123"}`
- **WHEN** parsed as `CustomerData`
- **THEN** Pydantic raises ValidationError (phone must be 10-15 digits)

#### Scenario: OrderCreate requires at least 1 item
- **GIVEN** a request body with `"items": []`
- **WHEN** parsed as `OrderCreate`
- **THEN** Pydantic raises ValidationError (items must have at least 1 element)

### Requirement: order number generation
The system MUST generate `numero_orden` in the format `ORD-YYYYMMDD-{6 hex chars}` where the hex chars come from `secrets.token_hex(3)`. The number is generated server-side at order creation time.

#### Scenario: numero_orden format
- **GIVEN** today is 2026-06-07
- **WHEN** an order is created
- **THEN** `numero_orden` matches the regex `^ORD-20260607-[0-9a-f]{6}$` (example: `ORD-20260607-a3f9b2`)

#### Scenario: numero_orden is unique
- **GIVEN** 1000 orders are created in the same day
- **WHEN** any two `numero_orden` values are compared
- **THEN** they are all distinct (collision probability is ~1 in 16 million, acceptable for MVP)

### Requirement: order persistence
The system MUST persist each `POST /ordenes` request as:
- 1 row in `clientes` (with the customer data — use `INSERT ... ON CONFLICT(telefono) DO UPDATE SET nombre=excluded.nombre, edad=excluded.edad, genero=excluded.genero` to upsert by phone)
- N rows in `ordenes` (one per cart item, with `cliente_id` set to the just-inserted/updated client)
- All in a SINGLE sqlite3 transaction (commit at the end, rollback on any error)

#### Scenario: new customer
- **GIVEN** no client exists with telefono "5551234567"
- **WHEN** an order is created with that phone
- **THEN** after the request, `SELECT COUNT(*) FROM clientes WHERE telefono='5551234567'` is 1, and the order's `cliente_id` matches

#### Scenario: repeat customer upserts
- **GIVEN** a client exists with telefono "5551234567" (nombre "Juan", edad 28)
- **WHEN** an order is created with telefono "5551234567", nombre "Juan Pérez", edad 29
- **THEN** the cliente row is updated (nombre and edad) and only 1 cliente row exists with that phone

#### Scenario: atomicity
- **GIVEN** a request with 2 items, but the second item's SKU doesn't exist in `productos`
- **WHEN** the order is created
- **THEN** the response is HTTP 404 with an error message, AND `SELECT COUNT(*) FROM clientes WHERE telefono=...` is 0 (the cliente was NOT created), AND no rows were added to `ordenes`

### Requirement: order response
The system MUST return an `OrderResponse` JSON on successful creation:

```python
class OrderResponse(BaseModel):
    numero_orden: str
    total: float
    whatsapp_url: str
    customer_name: str
```

#### Scenario: OrderResponse shape
- **GIVEN** a successful order creation
- **WHEN** the response is received
- **THEN** the JSON has all 4 fields and `total` is a positive float

### Requirement: order summary formatting (for WhatsApp)
The system MUST format the order as a multi-line Spanish text message in the format:

```
🐶 *Jochos El Perro Wero* — Pedido ORD-20260607-a3f9b2

*Cliente:* Juan Pérez
*Teléfono:* 5551234567

*Tu pedido:*
• 2x Jocho Clásico — $130
• 1x Hamburguesa con Tocino — $110

*Total:* $240

¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭
```

This text is built server-side in a helper function `format_order_message(ordenes, cliente) -> str`.

#### Scenario: message includes all items
- **GIVEN** an order with 2 items
- **WHEN** `format_order_message` is called
- **THEN** the returned string contains both item lines with their quantities, prices, and subtotals

#### Scenario: message is URL-safe encoded
- **GIVEN** a formatted order message
- **WHEN** it is URL-encoded for the `text` query param
- **THEN** special characters (em-dash, ñ, tildes) are percent-encoded correctly and the URL is valid

None — greenfield change.

None.
