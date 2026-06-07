# Capability: admin-ui

## Purpose
The four admin pages (dashboard, inventory, banner editor, orders viewer) and their backing routes. After authenticating via the `admin-auth` capability, the admin can manage the menu (toggle Sold Out per SKU), update the promo banner text, and see recent orders.

## Requirements

### Requirement: Pydantic models for admin
The system MUST add these models to `app/schemas.py`:

```python
class AdminLogin(BaseModel):
    password: str = Field(..., min_length=1, max_length=200)

class BannerUpdate(BaseModel):
    banner_text: str = Field(..., min_length=1, max_length=500)
```

#### Scenario: AdminLogin accepts non-empty password
- **GIVEN** a request with `{"password": "wero123"}`
- **WHEN** parsed as `AdminLogin`
- **THEN** it succeeds

#### Scenario: AdminLogin rejects empty password
- **GIVEN** a request with `{"password": ""}`
- **WHEN** parsed as `AdminLogin`
- **THEN** Pydantic raises `ValidationError`

#### Scenario: BannerUpdate accepts non-empty text
- **GIVEN** a request with `{"banner_text": "¡Nueva promo!"}`
- **WHEN** parsed as `BannerUpdate`
- **THEN** it succeeds

#### Scenario: BannerUpdate rejects empty text
- **GIVEN** a request with `{"banner_text": ""}`
- **WHEN** parsed as `BannerUpdate`
- **THEN** Pydantic raises `ValidationError`

#### Scenario: BannerUpdate rejects very long text
- **GIVEN** a request with 501+ character banner_text
- **WHEN** parsed as `BannerUpdate`
- **THEN** Pydantic raises `ValidationError`

### Requirement: dashboard route
The system MUST expose `GET /admin/` (auth required) that returns HTTP 200 with `admin/dashboard.html` showing:
- Welcome message: "¡Bienvenido al panel de administración, Wero!"
- 3 navigation cards: "Inventario" (→ /admin/inventario), "Banner" (→ /admin/banner), "Órdenes" (→ /admin/ordenes)
- A logout link in the topbar

#### Scenario: dashboard renders for authenticated admin
- **GIVEN** a valid `wero_admin` cookie
- **WHEN** `GET /admin/` is requested
- **THEN** the response is HTTP 200 with the dashboard HTML containing "Bienvenido", and links to /admin/inventario, /admin/banner, /admin/ordenes

#### Scenario: dashboard redirects unauthenticated
- **GIVEN** no `wero_admin` cookie
- **WHEN** `GET /admin/` is requested
- **THEN** the response is HTTP 303 with `Location: /admin/login`

### Requirement: inventory route
The system MUST expose `GET /admin/inventario` (auth required) that returns HTTP 200 with `admin/inventario.html` showing:
- A table of all products (id, sku, nombre, categoria, precio, disponible, actions)
- Each row has a "Toggle" button that POSTs to `/admin/inventario/{sku}/toggle`
- A success message is shown if `?updated={sku}` is in the query string

#### Scenario: inventory shows all products
- **GIVEN** a valid `wero_admin` cookie and 6 seed products
- **WHEN** `GET /admin/inventario` is requested
- **THEN** the response is HTTP 200 and the table has 6 rows (one per product)

#### Scenario: inventory shows toggle state correctly
- **GIVEN** a product with `disponible=0` and another with `disponible=1`
- **WHEN** the inventory page renders
- **THEN** the `disponible=0` row shows "Agotado" with an "Activar" button
- **AND** the `disponible=1` row shows "Disponible" with a "Desactivar" button

### Requirement: inventory toggle route
The system MUST expose `POST /admin/inventario/{sku}/toggle` (auth required) that:
- Looks up the product by SKU
- Flips `disponible` (0→1 or 1→0)
- Redirects to `GET /admin/inventario?updated={sku}` with HTTP 303

#### Scenario: toggle flips state
- **GIVEN** product JO-001 has `disponible=1` in the DB
- **WHEN** `POST /admin/inventario/JO-001/toggle` is called (with auth)
- **THEN** the DB now has `disponible=0` for JO-001
- **AND** the response is HTTP 303 with `Location: /admin/inventario?updated=JO-001`

#### Scenario: toggle redirects with confirmation
- **GIVEN** a valid toggle request
- **WHEN** the redirect is followed
- **THEN** the inventory page shows a success message "Producto JO-001 actualizado" (or similar)

#### Scenario: toggle non-existent SKU
- **GIVEN** a request for `POST /admin/inventario/FAKE-001/toggle`
- **WHEN** the route is called
- **THEN** the response is HTTP 404 (or the route just redirects without updating)

#### Scenario: home page reflects toggle
- **GIVEN** a toggle of JO-001 from `disponible=1` to `disponible=0`
- **WHEN** `GET /` is requested
- **THEN** the JO-001 product card in the menu grid shows the "Agotado" badge

### Requirement: banner editor route
The system MUST expose `GET /admin/banner` (auth required) that returns HTTP 200 with `admin/banner.html` showing a form with:
- A `<textarea name="banner_text">` pre-filled with the current `configuracion.banner_promocion`
- A "Guardar" submit button

#### Scenario: banner form is pre-filled
- **GIVEN** `configuracion.banner_promocion` is "¡SÚPER PROMO! 2 Hamburguesas con Tocino + Papas por $200"
- **WHEN** `GET /admin/banner` is requested
- **THEN** the form's textarea has the exact current value

#### Scenario: banner form is empty when config is missing
- **GIVEN** `configuracion.banner_promocion` row doesn't exist
- **WHEN** `GET /admin/banner` is requested
- **THEN** the form's textarea is empty (placeholder text "Escribe el texto del banner...")

### Requirement: banner update route
The system MUST expose `POST /admin/banner` (auth required) that:
- Accepts a form submission with `banner_text` field
- Updates (or inserts) `configuracion.banner_promocion` with the new value
- Redirects to `GET /admin/banner?updated=1` with HTTP 303

#### Scenario: banner update persists
- **GIVEN** a valid POST with `banner_text="¡Nueva promo de Wero!"`
- **WHEN** the route is called
- **THEN** the DB has `configuracion.banner_promocion = "¡Nueva promo de Wero!"`
- **AND** the response is HTTP 303 with `Location: /admin/banner?updated=1`

#### Scenario: banner update shows in home page
- **GIVEN** the banner was updated to "¡Nueva promo de Wero!"
- **WHEN** `GET /` is requested
- **THEN** the home page shows the new banner text in the hero section

#### Scenario: banner update with INSERT OR IGNORE
- **GIVEN** the `configuracion.banner_promocion` row was deleted
- **WHEN** a POST updates the banner
- **THEN** the row is re-inserted (using `INSERT OR IGNORE` or `INSERT OR REPLACE`)

### Requirement: orders viewer route
The system MUST expose `GET /admin/ordenes` (auth required) that returns HTTP 200 with `admin/ordenes.html` showing a table of the last 50 orders (ordered by `fecha_hora DESC`).

#### Scenario: orders table is empty initially
- **GIVEN** no orders in the DB
- **WHEN** `GET /admin/ordenes` is requested
- **THEN** the table is empty (or shows "Aún no hay pedidos" placeholder)

#### Scenario: orders table shows recent orders
- **GIVEN** 3 orders have been placed (via the public flow)
- **WHEN** `GET /admin/ordenes` is requested
- **THEN** the table shows 3 rows with: numero_orden, fecha_hora (formatted), customer nombre, total (sum of the order's lines), and a link to view the WhatsApp redirect

#### Scenario: orders are sorted newest first
- **GIVEN** 3 orders placed at different times
- **WHEN** the orders table renders
- **THEN** the most recent order is in the first row (ORDER BY fecha_hora DESC)

#### Scenario: total is computed per order
- **GIVEN** an order with 2 lines: (2, JO-001, 65) and (1, HB-002, 110)
- **WHEN** the orders table renders
- **THEN** the total column for that order is $240

### Requirement: admin topbar in base_admin.html
The system MUST modify `app/templates/base_admin.html` (from the foundation) to add:
- A logout link in the topbar pointing to `/admin/logout`
- Active-link highlighting for the current section (dashboard, inventario, banner, ordenes)

#### Scenario: topbar shows nav links
- **GIVEN** any admin page is rendered
- **WHEN** the HTML is inspected
- **THEN** the topbar contains links to: /admin/ (Dashboard), /admin/inventario, /admin/banner, /admin/ordenes, /admin/logout

#### Scenario: active link is highlighted
- **GIVEN** the user is on `/admin/inventario`
- **WHEN** the page renders
- **THEN** the "Inventario" link in the topbar has a special class (e.g., `.admin-topbar__link--active`) or style indicating it's the current page

### Requirement: admin CSS
The system MUST provide `app/static/css/admin.css` with styles for the admin pages:
- `.admin-dashboard` — grid of 3 nav cards
- `.admin-nav-card` — large clickable card with title + description + icon
- `.admin-table` — compact data table (smaller padding than the public tables)
- `.toggle-button` — green/red button that visually indicates the current state
- `.admin-form` — single-column form layout
- `.admin-flash` — green flash message banner for "updated" confirmations

The CSS file is loaded after `components.css` in `base_admin.html`.

#### Scenario: admin CSS is served
- **GIVEN** the server is running
- **WHEN** `GET /static/css/admin.css` is requested
- **THEN** the response is HTTP 200 with `Content-Type: text/css`

#### Scenario: admin page uses admin CSS
- **GIVEN** any admin page is rendered
- **WHEN** the HTML head is inspected
- **THEN** it includes `<link rel="stylesheet" href="/static/css/admin.css">` after `components.css`

### Requirement: visual identity consistency
The admin pages MUST use the same Mexican urban identity as the public pages:
- Royal Blue background or card backgrounds
- Magenta CTAs (e.g., "Guardar", "Activar", "Desactivar" buttons)
- Yellow highlights for prices
- Bebas Neue / Anton display fonts for headings
- Consistent topbar style with the public site's footer

#### Scenario: admin page has Mexican urban identity
- **GIVEN** any admin page is rendered
- **WHEN** the HTML and CSS are inspected
- **THEN** the colors and typography match the public site's identity (using the same `var(--color-magenta)`, `var(--color-amarillo)`, `var(--font-display)`, etc.)

## MODIFIED Requirements
None — greenfield change.

## REMOVED Requirements
None.
