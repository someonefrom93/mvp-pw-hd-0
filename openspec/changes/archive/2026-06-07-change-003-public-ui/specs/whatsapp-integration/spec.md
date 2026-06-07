# Capability: whatsapp-integration

## Purpose
The WhatsApp checkout integration. After a successful order creation, the server returns a `wa.me/{phone}?text={urlencoded_message}` URL that the browser follows to open WhatsApp (web or app) with the order summary pre-filled. No WhatsApp API key or business account required — `wa.me` works for any phone number and any device.

## Requirements

### Requirement: phone number from config
The system MUST read the business WhatsApp phone number from `configuracion.whatsapp_numero` (seed value: `525555555555` — Mexico country code + 10 digits). The value is stored without the `+` prefix (wa.me format).

#### Scenario: phone number is loaded from DB
- **GIVEN** `configuracion.whatsapp_numero` is "525555555555"
- **WHEN** an order is created
- **THEN** the resulting `whatsapp_url` contains `wa.me/525555555555`

#### Scenario: phone number is configurable
- **GIVEN** the admin updates `configuracion.whatsapp_numero` to "525551234567" (via change-004-admin-ui)
- **WHEN** a new order is created after the update
- **THEN** the resulting `whatsapp_url` contains `wa.me/525551234567`

### Requirement: whatsapp URL builder
The system MUST provide a helper function `build_whatsapp_url(phone: str, message: str) -> str` that returns `https://wa.me/{phone}?text={urllib.parse.quote(message, safe='')}`.

#### Scenario: basic URL build
- **GIVEN** `phone = "525555555555"` and `message = "Hola"`
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result is `"https://wa.me/525555555555?text=Hola"`

#### Scenario: special characters are encoded
- **GIVEN** `message = "Jochos 🌭 — $200"` (em-dash, emoji, dollar sign)
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result contains `%F0%9F%8C%BD` (emoji), `%E2%80%94` (em-dash), and `%24200` (dollar) — no raw special chars in the URL

#### Scenario: spaces become %20
- **GIVEN** `message = "Hola amigo"`
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result contains `%20` (not `+`, since wa.me uses standard URL encoding)

### Requirement: whatsapp redirect endpoint
The system MUST expose `GET /ordenes/{numero_orden}/whatsapp` that:
1. Looks up the order and customer in the DB
2. Builds the message using `format_order_message` (from cart-flow)
3. Returns HTTP 302 with `Location: {build_whatsapp_url(phone, message)}`

#### Scenario: successful redirect
- **GIVEN** an order `ORD-20260607-a3f9b2` exists with customer "Juan Pérez" and 2 items
- **WHEN** `GET /ordenes/ORD-20260607-a3f9b2/whatsapp` is called
- **THEN** the response is HTTP 302 and the `Location` header is `https://wa.me/525555555555?text=...` containing the full formatted message

#### Scenario: order not found returns 404
- **GIVEN** no order with `numero_orden = "ORD-DOES-NOT-EXIST"`
- **WHEN** `GET /ordenes/ORD-DOES-NOT-EXIST/whatsapp` is called
- **THEN** the response is HTTP 404 with body `{"detail": "Order not found"}`

#### Scenario: redirect is browser-friendly
- **GIVEN** the order exists
- **WHEN** the response is inspected
- **THEN** it has status code 302 (not 307) so older browsers also follow correctly, and the `Location` header is the full https URL

### Requirement: message content
The system MUST format the order message in Spanish with these sections in order:
1. **Header** with the brand name "🐶 *Jochos El Perro Wero* — Pedido {numero_orden}" (bold via WhatsApp `*...*` syntax)
2. **Customer block** with `*Cliente:* {nombre}` and `*Teléfono:* {telefono}`
3. **Items list** with one line per item: `• {cantidad}x {nombre} — ${subtotal}` (subtotal = precio × cantidad)
4. **Total** as `*Total:* ${total}` (bold)
5. **Closing line** in Spanish: "¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭"

#### Scenario: header includes brand and order number
- **GIVEN** the order's numero_orden is "ORD-20260607-a3f9b2"
- **WHEN** the message is formatted
- **THEN** the first line is `🐶 *Jochos El Perro Wero* — Pedido ORD-20260607-a3f9b2`

#### Scenario: each item line is formatted
- **GIVEN** an order with 2 items: (2, "Jocho Clásico", 65) and (1, "Hamburguesa con Tocino", 110)
- **WHEN** the message is formatted
- **THEN** the items section contains:
  - `• 2x Jocho Clásico — $130`
  - `• 1x Hamburguesa con Tocino — $110`

#### Scenario: total is computed correctly
- **GIVEN** the items above (130 + 110)
- **WHEN** the message is formatted
- **THEN** the total line is `*Total:* $240`

#### Scenario: closing line is in Spanish
- **GIVEN** any order
- **WHEN** the message is formatted
- **THEN** the last line is exactly "¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭"

### Requirement: works on mobile and desktop
The system MUST use the official `wa.me` URL pattern (not `api.whatsapp.com/send`) so the same URL works on both:
- **Mobile**: opens the WhatsApp app via universal link
- **Desktop**: opens `web.whatsapp.com` in a new tab

#### Scenario: URL is wa.me
- **GIVEN** any successful order
- **WHEN** the whatsapp_url is inspected
- **THEN** it starts with `https://wa.me/` (NOT `https://api.whatsapp.com/` or `https://web.whatsapp.com/`)

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
