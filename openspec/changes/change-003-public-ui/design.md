# Design: Change 003 — Public UI

## 1. Overview

Greenfield half of the umbrella `change-002-features`: the public client side of *Jochos El Perro Wero*. Adds the home page (`GET /`), an order creation endpoint (`POST /ordenes`) with Pydantic v2 validation, and a WhatsApp redirect route (`GET /ordenes/{numero_orden}/whatsapp`). A new `components.css` layer establishes the Mexican urban visual identity (Azul Rey + Magenta + Amarillo comic-book vibe) on top of the foundation's `tokens.css` + `main.css`. Cart state lives in the browser's `localStorage` via a tiny vanilla-JS `WeroCart` object — no build step, no framework. The admin UI lands in the follow-up `change-004-admin-ui`.

## 2. File Tree (this change only)

```
app/
├── schemas.py                          (NEW, ~70 LOC Pydantic v2 models)
├── routes/
│   └── public.py                       (MODIFIED, +3 routes ~100 LOC)
├── templates/
│   ├── base.html                       (MODIFIED, +1 link to components.css)
│   └── public/                         (NEW directory)
│       ├── home.html                   (NEW, ~80 LOC Jinja)
│       ├── order_pending.html          (NEW, ~30 LOC)
│       └── partials/
│           ├── product_card.html       (NEW, ~25 LOC)
│           └── cart_summary.html       (NEW, ~20 LOC)
└── static/
    ├── css/
    │   └── components.css              (NEW, ~250 LOC)
    ├── js/
    │   ├── cart.js                     (NEW, ~80 LOC)
    │   └── order.js                    (NEW, ~60 LOC)
    └── img/
        ├── wero-mascot.svg             (NEW, hand-crafted SVG)
        ├── placeholder-JO-001.svg      (NEW, 6 of these)
        ├── placeholder-JO-002.svg
        ├── placeholder-JO-003.svg
        ├── placeholder-HB-001.svg
        ├── placeholder-HB-002.svg
        └── placeholder-HB-003.svg
```

Modified (1 line): `pyproject.toml` — add `itsdangerous` to runtime deps.
Total: ~16 new files + 2 modified files, ~720 LOC.

## 3. Module Responsibilities

| File | Responsibility | Public symbols |
|------|----------------|----------------|
| `app/schemas.py` | Pydantic v2 request/response models for /ordenes | `CartItem`, `CustomerData`, `OrderCreate`, `OrderResponse` |
| `app/routes/public.py` | GET /, POST /ordenes, GET /ordenes/{id}/whatsapp | existing `router` (extended) |
| `app/templates/public/home.html` | Home page — banner, location, menu grid, social footer | — |
| `app/templates/public/order_pending.html` | "Gracias por tu pedido" page | — |
| `app/templates/public/partials/product_card.html` | Single product card (used in a loop) | — |
| `app/templates/public/partials/cart_summary.html` | Cart modal item list | — |
| `app/static/css/components.css` | All component styles (BEM-lite naming) | — |
| `app/static/js/cart.js` | WeroCart object + cart UI bindings | `WeroCart` (global) |
| `app/static/js/order.js` | Order form submit + redirect | — |
| `app/static/img/wero-mascot.svg` | Brand mascot illustration | — |
| `app/static/img/placeholder-*.svg` | Product image placeholders (6 files) | — |

## 4. CSS Architecture

### Load order (in `base.html` `<head>`)
1. `tokens.css` (already in main, from change-001) — design tokens on `:root`
2. `main.css` (already in main) — reset + typography
3. `components.css` (NEW) — component styles layered on top

The change to `base.html` is a single new `<link rel="stylesheet" href="/static/css/components.css">` line, inserted right after the existing `main.css` line, inside the same `<head>`. The `{% block extra_head %}` hook is not used here because the change is unconditional.

### Naming convention: BEM-lite
- Block: `.card`, `.btn`, `.modal`, `.hero-banner`
- Element: `.card__image`, `.card__title`, `.btn-magenta` (modifier as suffix)
- Modifier: `.card--soldout`, `.btn-block`, `.btn:disabled` (state)

### components.css structure
```
/* === BUTTONS === */
.btn, .btn-magenta, .btn-amarillo, .btn-outline, .btn-block, .btn:hover, .btn:active, .btn:disabled

/* === CARDS === */
.card, .card-producto, .card-producto:hover, .card--soldout, .card__badge-agotado

/* === HERO BANNER === */
.hero-banner, .hero-banner__starburst, .hero-banner__mascot

/* === LOCATION BLOCK === */
.location-block, .location-block__map, .location-block__pin

/* === MENU GRID === */
.menu-grid, .menu-grid__item

/* === FOOTER === */
.site-footer, .site-footer__col, .site-footer__social-link

/* === FORMS === */
.form-row, .form-label, .form-input, .form-input:focus, .form-error

/* === MODAL === */
.modal, .modal__backdrop, .modal__content, .modal__close, .modal--cart, .modal--open

/* === CART FAB === */
.cart-fab, .cart-fab__count, .cart-fab__pulse-animation

/* === UTILITIES === */
.container (max-width 1200px, centered), .visually-hidden (sr-only), .text-center, .text-magenta, .text-amarillo
```

### Responsive breakpoints
- Mobile-first
- `@media (min-width: 640px)` — small tablet: menu grid 2 columns
- `@media (min-width: 960px)` — desktop: menu grid 3 columns, footer 3 columns, hero banner mascot visible

## 5. JavaScript Architecture

### No build step
All JS is plain ES2020 (works in any modern browser). No bundler, no transpilation, no npm dependencies. Each file is a separate `<script>` tag in `home.html` (end of `body`), so file order is deterministic: `cart.js` defines `WeroCart` on `window` first, then `order.js` consumes it.

### Load order (in `home.html` end of body)
1. `cart.js` — defines `window.WeroCart`
2. `order.js` — uses `WeroCart` and posts to `/ordenes`

### WeroCart object (cart.js)
```js
const STORAGE_KEY = 'wero_cart_v1';

const WeroCart = (() => {
  let state = load();

  function load() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch { return {}; }
  }
  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    document.dispatchEvent(new CustomEvent('cart:change'));
  }
  return {
    items() { return Object.entries(state).map(([sku, cantidad]) => ({sku, cantidad})); },
    add(sku, qty=1) { state[sku] = (state[sku] || 0) + qty; save(); return this; },
    remove(sku) { delete state[sku]; save(); return this; },
    update(sku, qty) { if (qty <= 0) return this.remove(sku); state[sku] = qty; save(); return this; },
    clear() { state = {}; save(); return this; },
    count() { return Object.keys(state).length; },
    totalQty() { return Object.values(state).reduce((a, b) => a + b, 0); },
    isEmpty() { return this.count() === 0; },
  };
})();
window.WeroCart = WeroCart;

// On DOMContentLoaded: render initial cart UI
document.addEventListener('DOMContentLoaded', () => {
  // Update cart-fab count
  // Render cart modal contents
  // Hook "Añadir al carrito" buttons
  document.querySelectorAll('[data-sku]').forEach(btn => {
    btn.addEventListener('click', () => {
      const sku = btn.dataset.sku;
      const qty = parseInt(btn.closest('.card-producto').querySelector('input[type=number]').value, 10);
      WeroCart.add(sku, qty);
    });
  });
});
```

### order.js
```js
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('order-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const items = WeroCart.items();
    if (items.length === 0) { alert('Tu carrito está vacío'); return; }
    const formData = new FormData(form);
    const customer = {
      nombre: formData.get('nombre'),
      telefono: formData.get('telefono'),
      edad: parseInt(formData.get('edad'), 10),
      genero: formData.get('genero'),
    };
    const resp = await fetch('/ordenes', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({items, customer}),
    });
    if (!resp.ok) { alert('Error al crear el pedido'); return; }
    const data = await resp.json();
    WeroCart.clear();
    window.location.href = data.whatsapp_url;
  });
});
```

## 6. Pydantic Schemas (app/schemas.py)

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

## 7. Route Handlers (app/routes/public.py — additions)

```python
from datetime import date
import secrets
from urllib.parse import quote

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.models import Producto, ConfigKey
from app.schemas import OrderCreate, OrderResponse

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    with get_db() as conn:
        productos_rows = conn.execute(
            "SELECT * FROM productos ORDER BY categoria, sku"
        ).fetchall()
        productos = [Producto.from_row(r) for r in productos_rows]
        config_rows = conn.execute("SELECT llave, valor FROM configuracion").fetchall()
        config = {r["llave"]: r["valor"] for r in config_rows}
    return templates.TemplateResponse(
        "public/home.html",
        {"request": request, "productos": productos, "config": config},
    )


@router.post("/ordenes", response_model=OrderResponse)
def create_order(payload: OrderCreate) -> OrderResponse:
    with get_db() as conn:
        cur = conn.cursor()
        # Verify all SKUs exist
        skus = [item.sku for item in payload.items]
        placeholders = ",".join("?" * len(skus))
        found = cur.execute(
            f"SELECT sku, nombre, precio FROM productos WHERE sku IN ({placeholders})",
            skus,
        ).fetchall()
        if len(found) != len(skus):
            raise HTTPException(status_code=404, detail="Uno o más productos no existen")
        # Lookup or insert cliente
        cur.execute(
            "INSERT INTO clientes (nombre, telefono, edad, genero) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(telefono) DO UPDATE SET nombre=excluded.nombre, edad=excluded.edad, genero=excluded.genero",
            (payload.customer.nombre, payload.customer.telefono, payload.customer.edad, payload.customer.genero),
        )
        cliente_id = cur.execute(
            "SELECT id FROM clientes WHERE telefono = ?", (payload.customer.telefono,)
        ).fetchone()["id"]
        # Generate order number
        numero_orden = f"ORD-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(3)}"
        # Insert order lines
        total = 0.0
        price_map = {r["sku"]: (r["nombre"], r["precio"]) for r in found}
        for item in payload.items:
            nombre, precio = price_map[item.sku]
            cur.execute(
                "INSERT INTO ordenes (numero_orden, cliente_id, sku, producto, precio, cantidad) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (numero_orden, cliente_id, item.sku, nombre, precio, item.cantidad),
            )
            total += precio * item.cantidad
        # Get whatsapp phone
        phone_row = cur.execute(
            "SELECT valor FROM configuracion WHERE llave = 'whatsapp_numero'"
        ).fetchone()
        phone = phone_row["valor"] if phone_row else "525555555555"
        conn.commit()

    # Build whatsapp URL (after commit so we can query the just-inserted data)
    message = format_order_message(numero_orden, payload.customer.nombre, payload.customer.telefono, payload.items, price_map, total)
    whatsapp_url = f"https://wa.me/{phone}?text={quote(message, safe='')}"

    return OrderResponse(
        numero_orden=numero_orden,
        total=total,
        whatsapp_url=whatsapp_url,
        customer_name=payload.customer.nombre,
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
    phone = phone_row["valor"] if phone_row else "525555555555"
    items = [(r["sku"], r["producto"], r["precio"], r["cantidad"]) for r in order_rows]
    total = sum(r["precio"] * r["cantidad"] for r in order_rows)
    message = format_order_message(numero_orden, cliente["nombre"], cliente["telefono"], items, None, total)
    return RedirectResponse(url=f"https://wa.me/{phone}?text={quote(message, safe='')}", status_code=302)


def format_order_message(numero_orden, nombre, telefono, items, price_map, total) -> str:
    """Format an order as a Spanish WhatsApp message."""
    lines = [
        f"🐶 *Jochos El Perro Wero* — Pedido {numero_orden}",
        "",
        f"*Cliente:* {nombre}",
        f"*Teléfono:* {telefono}",
        "",
        "*Tu pedido:*",
    ]
    for item in items:
        # items can be dict (from OrderCreate) or tuple (from DB)
        if isinstance(item, dict):
            sku, cantidad = item["sku"], item["cantidad"]
            nombre_prod, precio = price_map[sku]
        else:
            sku, nombre_prod, precio, cantidad = item
        subtotal = precio * cantidad
        lines.append(f"• {cantidad}x {nombre_prod} — ${subtotal:.0f}")
    lines += ["", f"*Total:* ${total:.0f}", "", "¡Gracias por tu pedido! Confirma por aquí y te lo llevamos en un periquito 🌭"]
    return "\n".join(lines)
```

## 8. Template Hierarchy

```
base.html                                    (existing)
└── public/home.html                         (new, extends base)
    ├── includes partials/product_card.html  (in a loop over productos)
    └── includes partials/cart_summary.html  (inside the cart modal)
└── public/order_pending.html                (new, extends base)
    └── shows numero_orden + customer_name + "Continuar a WhatsApp" link
```

`home.html` uses `{% extends "base.html" %}` and overrides the `{% block content %}` and `{% block extra_scripts %}` blocks. The footer with social links lives in its own block — the cart-fab sits outside `<main>` so it's always visible. The `order_pending.html` is a thin page that the browser lands on if a user has JS disabled and submits the cart form via standard HTML POST fallback; in the normal flow the JS short-circuits straight to `whatsapp_url` so this template is mostly a graceful-degradation target.

## 9. Sequence — POST /ordenes

```
1. Browser clicks "Confirmar pedido"
2. order.js: form submit handler fires
3. order.js: WeroCart.items() → [{sku, cantidad}, ...]
4. order.js: build OrderCreate JSON
5. order.js: fetch('POST /ordenes', {body: JSON})
6. FastAPI: parses OrderCreate (Pydantic validation)
7. Route handler: opens DB transaction (get_db)
8.   7a. SELECT * FROM productos WHERE sku IN (...) — verify all SKUs exist
9.   7b. If missing → 404, transaction auto-rollback on context exit
10.  7c. INSERT ... ON CONFLICT(telefono) DO UPDATE for cliente
11.  7d. SELECT id FROM clientes WHERE telefono = ?
12.  7e. Generate numero_orden = ORD-{YYYYMMDD}-{6 hex}
13.  7f. INSERT INTO ordenes (loop over items)
14.  7g. SELECT valor FROM configuracion WHERE llave='whatsapp_numero'
15.  7h. conn.commit()
16. Route handler: format_order_message(...)
17. Route handler: build_whatsapp_url(phone, message)
18. Route handler: return OrderResponse JSON
19. order.js: WeroCart.clear()
20. order.js: window.location.href = data.whatsapp_url
21. Browser navigates to wa.me/... (opens WhatsApp web or app)
```

## 10. Mascot SVG Approach

Hand-crafted ~50-line SVG with:
- `<svg viewBox="0 0 200 200">`
- A yellow rounded-rect body (literal `#FACC15` — SVGs don't see CSS custom properties, so values are inlined; this matches the `--color-amarillo` token)
- A magenta mohawk (3-5 triangles on top of head, `#D62293`)
- Black sunglasses (2 ellipses)
- A spiked collar (5 triangles in a row)
- A hot dog in one paw (simplified)
- ViewBox 200x200, max width 200px in CSS

The mascot is rendered once in `home.html` inside `.hero-banner__mascot` and is hidden on mobile via CSS (`@media (max-width: 639px) { .hero-banner__mascot { display: none; } }`). Stays under 2KB uncompressed.

## 11. Product Placeholders

6 simple SVGs (one per SKU), generated programmatically. Each is a 400x400 viewBox with:
- Linear gradient: magenta → yellow, top-left to bottom-right
- Centered text: "JOCHO CLÁSICO" (or product name in display font)
- Subtitle: "PLACEHOLDER" in body font, smaller
- A "🐶" emoji in the bottom-right corner (works in SVG via `<text>` with an emoji-supporting font)

These are static files (no server-side generation). They can be hand-written once or generated by a small script during sdd-apply (not required). The sdd-apply task may include a one-shot generator script that writes all 6 files from the seed product names; this is optional. The 6 filenames are deterministic: `placeholder-{sku}.svg`.

## 12. Key Decisions and Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build step | None (vanilla JS, no bundler) | MVP; faster iteration; smaller learning curve |
| Cart state | localStorage (key `wero_cart_v1`) | No session required; survives reload; easy |
| Customer upsert | ON CONFLICT(telefono) DO UPDATE | Avoids duplicate client rows; phone is a natural unique ID for street-food customers |
| Order numbering | ORD-{YYYYMMDD}-{6 hex} | Human-readable date + short random suffix; collision ~1/16M |
| `quote(message, safe='')` | URL-encode everything including `/` | wa.me expects fully URL-encoded text |
| Modal cart vs page cart | Modal (slide-in from right on mobile) | Less context switching; faster checkout |
| Sold-out detection | Query `disponible=1` only | Server-side filter; client just shows what's in the products list |
| Placeholder images | 6 SVGs (one per SKU) | Deterministic; small; no image hosting needed |
| Pydantic version | v2 (FastAPI 0.110+ requires) | Use `Field(..., min_length=...)` and `pattern=...` |
| `itsdangerous` dep | Added to runtime deps (forward compat) | Used by change-004 for admin session, but listed here |
| Customer phone format | 10-15 digits, no `+` prefix | Mexico phones are 10 digits; allow international without `+` |
| Atomicity | Single sqlite3 transaction with `commit()` at end | If any INSERT fails, the cliente + ordenes are rolled back together |
| Form vs JSON for order | JSON (Content-Type: application/json) | Faster; Pydantic-native; no multipart parsing |
| `get_db()` reuse | Per-request context manager (foundation pattern) | The foundation already establishes this; no new DB connection code needed |
| Static mount | Already at `/static` in `app/main.py` (foundation) | SVGs served at `/static/img/...` automatically — no new wiring |
| Starburst shape | CSS `clip-path: polygon(...)` (24 points) | No image asset; scalable; smaller than an SVG star |
| Cart icon | Inline SVG in `cart-fab` | No external icon font; one less HTTP request |
| Itsdangerous on pyproject | Listed but unused this change | change-004 needs it; avoids a 2nd pyproject edit on the next change |

## 13. Out of Scope (deferred to change-004-admin-ui)

- Admin login screen and password validation
- Admin inventory panel (toggling `disponible` for each SKU)
- Admin banner editor (updating `configuracion.banner_promocion`)
- Admin orders viewer (dataframe of recent orders)
- Admin auth (signed cookie via itsdangerous)
- `AdminLogin` and `BannerUpdate` Pydantic models

## 14. Risks

- **LOC budget**: 450-550 forecast vs 400 budget → ~25% over. If `sdd-apply` trends > 500, split out `cart-flow` or `whatsapp-integration` into a 4th sub-change.
- **localStorage lost on browser clear**: documented in UI; acceptable for MVP
- **Pydantic v2 syntax**: tested with FastAPI 0.110+; no v1 compatibility needed
- **WhatsApp encoding**: test with em-dash (—), ñ, $, emoji, newline
- **Phone uniqueness**: edge case where 2 customers share a phone is rare; upsert handles it correctly
- **SQLite concurrent writes**: single-process app; no contention
- **SVG mascot in older browsers**: pure SVG works everywhere modern
- **`Field(pattern=...)` for phone**: Pydantic v2 syntax; verified
- **Templates coupling**: `home.html` is a 2nd top-level page after `base.html`; if the foundation adds more shared partials later, refactor is non-trivial
- **Forward dep on itsdangerous**: dep added now for change-004; if change-004 ships with a different plan, the dep just sits unused (harmless)

## 15. Smoke Test (for sdd-verify)

```bash
# Boot
uvicorn app.main:app --reload

# 1. Home page loads
curl -fsS http://127.0.0.1:8000/ | grep -q "Jochos El Perro Wero"

# 2. CSS components served
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/css/components.css  # 200

# 3. JS files served
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/js/cart.js   # 200
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/js/order.js  # 200

# 4. SVG assets served
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/img/wero-mascot.svg          # 200
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/static/img/placeholder-JO-001.svg  # 200

# 5. POST /ordenes creates order
curl -fsS -X POST http://127.0.0.1:8000/ordenes \
  -H "Content-Type: application/json" \
  -d '{"items":[{"sku":"JO-001","cantidad":2}],"customer":{"nombre":"Test","telefono":"5551111111","edad":30,"genero":"M"}}'
# → {"numero_orden":"ORD-...","total":130.0,"whatsapp_url":"https://wa.me/...","customer_name":"Test"}

# 6. DB has the order
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM ordenes;"  # → 1
sqlite3 el_perro_wero.db "SELECT COUNT(*) FROM clientes;"  # → 3 (was 2)

# 7. WhatsApp redirect
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8000/ordenes/ORD-.../whatsapp
# → 302 https://wa.me/...

# 8. Invalid cart returns 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/ordenes -H "Content-Type: application/json" -d '{"items":[],"customer":{...}}'
# → 422

# 9. Sold-out toggle works
sqlite3 el_perro_wero.db "UPDATE productos SET disponible=0 WHERE sku='JO-001';"
curl -fsS http://127.0.0.1:8000/ | grep -q "Agotado"  # sold-out badge appears
```

## 16. Dependencies

- `itsdangerous>=2.1` — added to runtime deps (for change-004 forward compat)
- No new third-party JS deps (vanilla only)
- Modern browser with CSS Grid, `clip-path`, `localStorage`, ES2020

## Cross-references

- Proposal: `proposal.md` (this change)
- Specs: `specs/{public-ui,component-css,cart-flow,whatsapp-integration}/spec.md`
- Foundation design: `../archive/2026-06-07-change-001-foundation/design.md`
- Umbrella: `../change-002-features/proposal.md`
- Companion (lands second): `../change-004-admin-ui/` (planned)
