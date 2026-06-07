# Capability: whatsapp-message

## Purpose
The server-side helpers for formatting an order as a Spanish WhatsApp message and building the `wa.me/{phone}?text={urlencoded_message}` URL. The text is human-readable, in Mexican Spanish, with WhatsApp markdown (`*bold*`, emoji), and is safe to URL-encode.

## Requirements

### Requirement: format_order_message helper
The system MUST provide a function `format_order_message(numero_orden, nombre, telefono, items, price_map, total) -> str` in `app/routes/public.py` that returns a multi-line string in the format:

```
🐶 *Jochos El Perro Wero* — Pedido {numero_orden}

*Cliente:* {nombre}
*Teléfono:* {telefono}

*Tu pedido:*
• {cantidad}x {nombre_producto} — ${subtotal}
• {cantidad}x {nombre_producto} — ${subtotal}

*Total:* ${total}

¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭
```

The function handles two `items` shapes:
- From `OrderCreate`: list of `CartItem` dataclass-like dicts `{sku, cantidad}` (use `price_map` to look up nombre + precio)
- From the DB: list of `(sku, nombre, precio, cantidad)` tuples (use directly, ignore `price_map`)

#### Scenario: message from OrderCreate
- **GIVEN** `format_order_message("ORD-20260607-abc123", "Juan Pérez", "5551234567", [CartItem(sku="JO-001", cantidad=2), CartItem(sku="HB-002", cantidad=1)], {"JO-001": ("Jocho Clásico", 65.0), "HB-002": ("Hamburguesa con Tocino", 110.0)}, 240.0)` is called
- **WHEN** the result is examined
- **THEN** the first line is `🐶 *Jochos El Perro Wero* — Pedido ORD-20260607-abc123`
- **AND** the items section contains `• 2x Jocho Clásico — $130` and `• 1x Hamburguesa con Tocino — $110`
- **AND** the total line is `*Total:* $240`
- **AND** the last line is `¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭`

#### Scenario: message from DB tuples
- **GIVEN** `format_order_message("ORD-...", "Juan", "555...", [("JO-001", "Jocho Clásico", 65.0, 2), ("HB-002", "Hamburguesa con Tocino", 110.0, 1)], None, 240.0)` is called
- **WHEN** the result is examined
- **THEN** the items section contains the same lines as above (the function uses the tuples directly, ignoring `price_map`)

#### Scenario: subtotal is integer-formatted
- **GIVEN** an item with precio=65.0 and cantidad=2 (subtotal=130.0)
- **WHEN** the message is formatted
- **THEN** the item line shows `$130` (not `$130.0`)

#### Scenario: total is integer-formatted
- **GIVEN** a total of 240.0
- **WHEN** the message is formatted
- **THEN** the total line shows `$240` (not `$240.0`)

#### Scenario: zero-decimal prices
- **GIVEN** an item with precio=50.0 (whole number)
- **WHEN** the subtotal is computed
- **THEN** the item line shows `$50` (not `$50.00` or `$50.0`)

### Requirement: build_whatsapp_url helper
The system MUST provide a function `build_whatsapp_url(phone: str, message: str) -> str` that returns `f"https://wa.me/{phone}?text={quote(message, safe='')}"`.

#### Scenario: basic URL build
- **GIVEN** `phone = "525555555555"` and `message = "Hola"`
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result is `"https://wa.me/525555555555?text=Hola"`

#### Scenario: special characters are encoded
- **GIVEN** `message = "Jochos 🌭 — $200"` (em-dash, emoji, dollar sign)
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result contains `%F0%9F%8C%BD` (emoji), `%E2%80%94` (em-dash), and `%24200` (dollar)
- **AND** no raw special chars remain in the URL

#### Scenario: spaces become %20
- **GIVEN** `message = "Hola amigo"`
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result contains `%20` (not `+`, since wa.me uses standard URL encoding)

#### Scenario: newlines are encoded
- **GIVEN** `message = "Line 1\nLine 2"`
- **WHEN** `build_whatsapp_url` is called
- **THEN** the result contains `%0A` (the URL-encoded newline)

#### Scenario: slashes are encoded
- **GIVEN** `message = "Jochos / Hamburguesas"`
- **WHEN** `build_whatsapp_url` is called with `safe=''`
- **THEN** the slash is encoded as `%2F`

### Requirement: phone number source
The system MUST read the business WhatsApp phone from `configuracion.whatsapp_numero` (seed value: `525555555555` — Mexico country code + 10 digits, no `+` prefix). The value is stored without the `+` prefix (wa.me format).

#### Scenario: phone is loaded from DB
- **GIVEN** `configuracion.whatsapp_numero` is "525555555555"
- **WHEN** an order is created or a redirect is built
- **THEN** the resulting `whatsapp_url` contains `wa.me/525555555555`

#### Scenario: phone is configurable
- **GIVEN** the admin updates `configuracion.whatsapp_numero` to "525551234567" (via `change-005-admin-ui`)
- **WHEN** a new order is created after the update
- **THEN** the resulting `whatsapp_url` contains `wa.me/525551234567`

#### Scenario: phone missing falls back to default
- **GIVEN** `configuracion.whatsapp_numero` row doesn't exist (rare; admin deleted it)
- **WHEN** an order is created
- **THEN** the system uses the fallback phone "525555555555" and the order still completes

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
- **GIVEN** any successful order or redirect
- **WHEN** the whatsapp_url is inspected
- **THEN** it starts with `https://wa.me/` (NOT `https://api.whatsapp.com/` or `https://web.whatsapp.com/`)

#### Scenario: redirect works in browser
- **GIVEN** a customer is on a mobile device
- **WHEN** they submit an order and the browser follows the `whatsapp_url`
- **THEN** the WhatsApp app opens (or the App Store / Play Store if not installed)
- **AND** the order message is pre-filled in the "new message" composer

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
