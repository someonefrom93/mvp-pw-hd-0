# Capability: public-ui

## Purpose
The public-facing home page (`GET /`), the order creation endpoint (`POST /ordenes`), and the WhatsApp redirect route (`GET /ordenes/{numero_orden}/whatsapp`). The home page is the brand's front door — banner, location, interactive menu, social buttons, and a flow that ends in a WhatsApp message to the business.

## Requirements

### Requirement: home page route
The system MUST expose `GET /` that returns HTTP 200 with `text/html; charset=utf-8` and renders the `home.html` template.

#### Scenario: home page loads with all sections
- **GIVEN** the foundation is in main and the DB has 6 products in the `productos` table
- **WHEN** a user visits `GET /` in a browser
- **THEN** the response is HTTP 200 and the rendered HTML contains the dynamic banner, the location/hours block, the menu grid with 6 product cards, the social media buttons (Facebook + DiDi Food), and the footer

#### Scenario: home page is responsive at 320px
- **GIVEN** the home page is loaded
- **WHEN** the viewport is 320px wide (iPhone SE)
- **THEN** the menu grid wraps to a single column, the banner is full-width, and no horizontal scroll appears

#### Scenario: home page is responsive at 1024px
- **GIVEN** the home page is loaded
- **WHEN** the viewport is 1024px wide
- **THEN** the menu grid shows 3 columns and the layout uses the full width gracefully

### Requirement: home page template structure
The system MUST provide `app/templates/public/home.html` that extends `base.html` and contains these blocks/sections in order:
1. **Hero banner** (`.hero-banner`) with the text from `configuracion.banner_promocion` rendered inside a starburst callout
2. **Location/hours** (`.location-block`) with the text from `configuracion.ubicacion_texto` and a placeholder map area (`.map-placeholder`) showing "Paseos del Pedregal" with a pin icon
3. **Menu grid** (`.menu-grid`) with a card for each available product (loaded from `productos` table where `disponible=1`) using the `product_card.html` partial
4. **Cart trigger** — a fixed-position cart button (`.cart-fab`) showing the current item count, opens the cart modal when clicked
5. **Footer** (`.site-footer`) with the Facebook and DiDi Food social links (URLs from `configuracion.facebook_url` and `configuracion.didi_food_url`) and the schedule

#### Scenario: hero banner shows DB-driven text
- **GIVEN** `configuracion.banner_promocion` is set to "¡SÚPER PROMO! 2 Hamburguesas con Tocino + Papas por $200"
- **WHEN** the home page is rendered
- **THEN** the banner HTML contains that exact text inside a starburst element

#### Scenario: menu grid filters sold-out products
- **GIVEN** 6 products in the `productos` table, 2 of which have `disponible=0`
- **WHEN** the home page is rendered
- **THEN** the menu grid shows all 6 products, but the 2 sold-out products render with the `card--soldout` class and a visible "Agotado" badge, and their "Añadir al carrito" button is disabled

### Requirement: product card partial
The system MUST provide `app/templates/public/partials/product_card.html` that takes a `Producto` dataclass and renders:
- The product image (placeholder SVG at `/static/img/placeholder-{sku}.svg`)
- The product name (uppercase, display font)
- The product description (body font)
- The price formatted as "$XX" (yellow starburst badge)
- An "Añadir al carrito" button (data-attribute `data-sku="{sku}"` for the cart JS to hook into)
- A "Cantidad" number input (default 1, min 1, max 20) next to the button
- If `disponible=0`: badge "Agotado" (replaces the button), the card gets `card--soldout` class, and the quantity input is hidden

#### Scenario: available product card
- **GIVEN** a `Producto(sku="JO-001", nombre="Jocho Clásico", precio=65.0, disponible=True)` is passed to the partial
- **WHEN** the partial is rendered
- **THEN** the output contains "JOCHO CLÁSICO" (uppercase), "$65" (price badge), an enabled "Añadir al carrito" button with `data-sku="JO-001"`, and NO "Agotado" badge

#### Scenario: sold-out product card
- **GIVEN** a `Producto(sku="JO-002", ..., disponible=False)` is passed to the partial
- **WHEN** the partial is rendered
- **THEN** the output contains an "Agotado" badge, NO "Añadir al carrito" button, the card has class `card--soldout`, and the quantity input is hidden

### Requirement: order creation route
The system MUST expose `POST /ordenes` that accepts a JSON body matching the `OrderCreate` Pydantic schema, validates it, creates one `clientes` row and N `ordenes` rows in a single transaction, generates a unique `numero_orden`, and returns a JSON `OrderResponse`.

#### Scenario: successful order creation
- **GIVEN** the request body is `{"items": [{"sku": "JO-001", "cantidad": 2}, {"sku": "HB-002", "cantidad": 1}], "customer": {"nombre": "Juan Pérez", "telefono": "5551234567", "edad": 28, "genero": "M"}}`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 200 with body `{"numero_orden": "ORD-20260607-abc123", "total": 240.0, "whatsapp_url": "https://wa.me/525555555555?text=..."}`
- **AND** the DB has 1 new row in `clientes` (with the customer data) and 2 new rows in `ordenes` (one per cart item)

#### Scenario: invalid customer data returns 422
- **GIVEN** the request body has a customer with `edad=-5` (invalid)
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 422 with a Pydantic validation error body

#### Scenario: empty cart returns 422
- **GIVEN** the request body has `"items": []`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 422 with a validation error explaining "at least 1 item required"

#### Scenario: order is atomic
- **GIVEN** the request body has 2 items but the second item's SKU doesn't exist in `productos`
- **WHEN** `POST /ordenes` is called
- **THEN** the response is HTTP 404 (or 422) and **no rows** are written to `clientes` or `ordenes` (transaction rolled back)

#### Scenario: total is computed correctly
- **GIVEN** a request with JO-001 (precio=65) x2 and HB-002 (precio=110) x1
- **WHEN** `POST /ordenes` is called
- **THEN** the response's `total` field is `240.0` (65*2 + 110*1)

### Requirement: whatsapp redirect route
The system MUST expose `GET /ordenes/{numero_orden}/whatsapp` that returns HTTP 302 with a `Location` header pointing to a `wa.me/{phone}?text={urlencoded_message}` URL.

#### Scenario: whatsapp URL is correct
- **GIVEN** an order with `numero_orden="ORD-20260607-abc123"`, items `[("JO-001", "Jocho Clásico", 65, 2), ("HB-002", "Hamburguesa con Tocino", 110, 1)]`, and customer "Juan Pérez" (tel "5551234567")
- **WHEN** `GET /ordenes/ORD-20260607-abc123/whatsapp` is called
- **THEN** the response is HTTP 302 and the `Location` header is `https://wa.me/525555555555?text=...` where the text parameter contains: business name "Jochos El Perro Wero", order number "ORD-20260607-abc123", customer name, and a line-by-line breakdown of the items with quantities and subtotals

#### Scenario: order not found returns 404
- **GIVEN** no order with `numero_orden="ORD-DOES-NOT-EXIST"`
- **WHEN** `GET /ordenes/ORD-DOES-NOT-EXIST/whatsapp` is called
- **THEN** the response is HTTP 404

### Requirement: order pending page
The system MUST provide `app/templates/public/order_pending.html` that extends `base.html`, shows the order number prominently, the customer a thank-you message in Spanish ("¡Gracias por tu pedido, [nombre]!"), and a "Continuar a WhatsApp" link to the `/ordenes/{numero_orden}/whatsapp` route.

#### Scenario: pending page shows order details
- **GIVEN** the order was created and the page is rendered with `{"numero_orden": "ORD-20260607-abc123", "customer_name": "Juan"}`
- **WHEN** the page renders
- **THEN** the HTML contains "ORD-20260607-abc123" prominently, "¡Gracias por tu pedido, Juan!" in Spanish, and a link to `/ordenes/ORD-20260607-abc123/whatsapp`

### Requirement: javascript modules
The system MUST provide two vanilla JS modules (no build step, loaded via `<script>` in `home.html`):
- `app/static/js/cart.js` — `WeroCart` object with methods: `add(sku, qty)`, `remove(sku)`, `update(sku, qty)`, `clear()`, `count()`, `total()`, `items()`. Backed by `localStorage` key `wero_cart_v1`. Emits a `cart:change` custom event on the document.
- `app/static/js/order.js` — handles the "Confirmar pedido" form submit, reads the cart from `WeroCart`, builds the `OrderCreate` payload, POSTs to `/ordenes`, then `window.location.href = response.whatsapp_url` on success.

#### Scenario: cart add and persist
- **GIVEN** the user is on the home page with no prior cart
- **WHEN** they click "Añadir al carrito" on JO-001 with quantity 2
- **THEN** `localStorage.wero_cart_v1` is `{"JO-001": 2}` and the cart-fab count badge updates to "1" (one distinct SKU)

#### Scenario: cart persists across reload
- **GIVEN** `localStorage.wero_cart_v1` is `{"JO-001": 2, "HB-002": 1}`
- **WHEN** the user reloads the page
- **THEN** the cart-fab count badge shows "2" and the cart modal shows both items

#### Scenario: order submission redirects to WhatsApp
- **GIVEN** the cart has 2 items and the customer form is filled
- **WHEN** the user clicks "Confirmar pedido"
- **THEN** a POST is sent to `/ordenes` with the correct payload, the response's `whatsapp_url` is followed (browser navigates to wa.me), and the cart is cleared

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
