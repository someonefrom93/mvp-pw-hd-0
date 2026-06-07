# Design: Change 005 — Admin UI

## 1. Overview

The hidden admin panel for "Jochos El Perro Wero": password login with signed cookie session, inventory panel to toggle Sold Out per SKU, banner editor for the promo text, and orders viewer. Auth is enforced via FastAPI `Depends(get_current_admin)` which returns a `RedirectResponse` if the cookie is missing or invalid. ~330 LOC total.

## 2. File Tree (this change only)

```
app/
├── auth.py                          (NEW, ~55 LOC — password check, signed cookie helpers, dependency)
├── schemas.py                       (MODIFIED, +15 LOC — AdminLogin, BannerUpdate)
├── routes/
│   └── admin.py                     (MODIFIED, +7 routes ~150 LOC)
└── templates/
    ├── base_admin.html              (MODIFIED, +logout link, active-link highlighting)
    └── admin/                       (NEW directory)
        ├── login.html                (~30 LOC)
        ├── dashboard.html            (~30 LOC)
        ├── inventario.html           (~45 LOC)
        ├── banner.html               (~30 LOC)
        └── ordenes.html              (~40 LOC)

app/static/css/
└── admin.css                        (NEW, ~80 LOC)
```

Total: 5 new files + 3 modified, ~345 LOC.

## 3. Module Responsibilities

| File | Responsibility | Public symbols |
|------|----------------|----------------|
| `app/auth.py` | Password check, signed cookie session, auth dependency | `ADMIN_PASSWORD`, `SECRET_KEY`, `check_password`, `create_session_token`, `verify_session_token`, `get_current_admin` |
| `app/schemas.py` | Pydantic models (modified) | `AdminLogin`, `BannerUpdate` (new); existing unchanged |
| `app/routes/admin.py` | Admin routes | `router` (existing) + 7 new routes |
| `app/templates/admin/login.html` | Password form | — |
| `app/templates/admin/dashboard.html` | Admin home with nav cards | — |
| `app/templates/admin/inventario.html` | Product list with toggles | — |
| `app/templates/admin/banner.html` | Banner editor form | — |
| `app/templates/admin/ordenes.html` | Recent orders table | — |
| `app/static/css/admin.css` | Admin-specific styles | — |

## 4. Authentication Flow

```
1. Admin visits GET /admin/inventario (or any /admin/* route)
2. The route has `Depends(get_current_admin)`
3. get_current_admin reads the `wero_admin` cookie
4. If cookie is missing or invalid:
   a. Returns RedirectResponse(url="/admin/login", status_code=303)
   b. FastAPI short-circuits the endpoint and returns the 303
   c. Browser follows the redirect → /admin/login
5. If cookie is valid:
   a. get_current_admin returns "admin" (string)
   b. The endpoint function runs normally
```

Login flow:
```
1. Admin visits GET /admin/login
2. Form is rendered (200)
3. Admin submits POST /admin/login with password=wero123
4. Route checks password with `check_password(submitted)`
5. If wrong: re-render login form with error message (200)
6. If right:
   a. `token = create_session_token()` (signed with SECRET_KEY, 7-day expiry)
   b. `response.set_cookie("wero_admin", token, httponly=True, max_age=604800, path="/", samesite="lax")`
   c. Return RedirectResponse(url="/admin/", status_code=303)
7. Browser follows the redirect → /admin/
8. Subsequent requests include the cookie → auth passes
```

Logout flow:
```
1. Admin clicks "Salir" link → GET /admin/logout
2. Route: `response.delete_cookie("wero_admin", path="/")`
3. Return RedirectResponse(url="/admin/login", status_code=303)
```

## 5. app/auth.py (sketch)

```python
import os
import secrets

from fastapi import Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

# Plain text for MVP. Replace with bcrypt + user table for production.
ADMIN_PASSWORD = "wero123"

# Overridable via env for production deployments
SECRET_KEY = os.environ.get("WERO_SECRET_KEY", "wero-dev-secret-change-me-in-production")

_signer = TimestampSigner(SECRET_KEY)


def check_password(submitted: str) -> bool:
    """Constant-time password comparison."""
    return secrets.compare_digest(submitted, ADMIN_PASSWORD)


def create_session_token() -> str:
    """Create a signed session token valid for 7 days."""
    return _signer.sign(b"admin").decode()


def verify_session_token(token: str) -> bool:
    """Return True if the token is valid and not expired."""
    if not token:
        return False
    try:
        _signer.unsign(token, max_age=7 * 24 * 60 * 60)
        return True
    except (BadSignature, SignatureExpired):
        return False


def get_current_admin(request: Request):
    """FastAPI dependency. Returns 'admin' if authenticated, or a RedirectResponse to /admin/login."""
    token = request.cookies.get("wero_admin")
    if not token or not verify_session_token(token):
        return RedirectResponse(url="/admin/login", status_code=303)
    return "admin"
```

## 6. app/routes/admin.py (additions)

```python
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    ADMIN_PASSWORD,
    check_password,
    create_session_token,
    get_current_admin,
)
from app.db import get_db
from app.models import Producto
from app.schemas import BannerUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    # If already authenticated, redirect to dashboard
    token = request.cookies.get("wero_admin")
    if token and _verify_token(token):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": None}
    )


@router.post("/login")
def login_submit(
    request: Request,
    password: str = Form(...),
):
    if not check_password(password):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Contraseña incorrecta"},
            status_code=200,
        )
    token = create_session_token()
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        "wero_admin", token,
        httponly=True, max_age=7*24*60*60, path="/", samesite="lax",
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("wero_admin", path="/")
    return response


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, admin: str = Depends(get_current_admin)):
    if isinstance(admin, RedirectResponse):
        return admin
    return templates.TemplateResponse(
        "admin/dashboard.html", {"request": request}
    )


@router.get("/inventario", response_class=HTMLResponse)
def inventario(
    request: Request,
    updated: str | None = None,
    admin: str = Depends(get_current_admin),
):
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM productos ORDER BY categoria, sku").fetchall()
        productos = [Producto.from_row(r) for r in rows]
    return templates.TemplateResponse(
        "admin/inventario.html",
        {"request": request, "productos": productos, "updated": updated},
    )


@router.post("/inventario/{sku}/toggle")
def toggle_inventario(sku: str, admin: str = Depends(get_current_admin)):
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        conn.execute(
            "UPDATE productos SET disponible = 1 - disponible WHERE sku = ?",
            (sku,),
        )
        conn.commit()
    return RedirectResponse(url=f"/admin/inventario?updated={sku}", status_code=303)


@router.get("/banner", response_class=HTMLResponse)
def banner_form(
    request: Request,
    updated: int | None = None,
    admin: str = Depends(get_current_admin),
):
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        row = conn.execute(
            "SELECT valor FROM configuracion WHERE llave = 'banner_promocion'"
        ).fetchone()
    current = row["valor"] if row else ""
    return templates.TemplateResponse(
        "admin/banner.html",
        {"request": request, "current_banner": current, "updated": updated},
    )


@router.post("/banner")
def banner_update(
    banner_text: str = Form(...),
    admin: str = Depends(get_current_admin),
):
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        conn.execute(
            "INSERT INTO configuracion (llave, valor) VALUES ('banner_promocion', ?) "
            "ON CONFLICT(llave) DO UPDATE SET valor = excluded.valor",
            (banner_text,),
        )
        conn.commit()
    return RedirectResponse(url="/admin/banner?updated=1", status_code=303)


@router.get("/ordenes", response_class=HTMLResponse)
def ordenes(request: Request, admin: str = Depends(get_current_admin)):
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        # Get last 50 orders with their totals
        orders_rows = conn.execute("""
            SELECT numero_orden, fecha_hora, cliente_id,
                   SUM(precio * cantidad) as total,
                   COUNT(*) as num_items
            FROM ordenes
            GROUP BY numero_orden
            ORDER BY fecha_hora DESC
            LIMIT 50
        """).fetchall()
        orders = []
        for r in orders_rows:
            cliente = conn.execute(
                "SELECT nombre, telefono FROM clientes WHERE id = ?",
                (r["cliente_id"],),
            ).fetchone()
            orders.append({
                "numero_orden": r["numero_orden"],
                "fecha_hora": r["fecha_hora"],
                "total": r["total"],
                "num_items": r["num_items"],
                "customer_name": cliente["nombre"] if cliente else "N/A",
            })
    return templates.TemplateResponse(
        "admin/ordenes.html", {"request": request, "orders": orders}
    )
```

## 7. Template Hierarchy

```
base.html                                    (existing)
└── base_admin.html                          (existing, modified to add nav + logout)
    ├── admin/login.html                     (new)
    ├── admin/dashboard.html                 (new)
    ├── admin/inventario.html                (new)
    ├── admin/banner.html                    (new)
    └── admin/ordenes.html                   (new)
```

`base_admin.html` modifications:
- Add `<link rel="stylesheet" href="/static/css/admin.css">` after `components.css`
- Add topbar nav: `Dashboard | Inventario | Banner | Órdenes | Salir`
- Active link highlighting: check `request.url.path` against each route

## 8. Key Decisions and Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth mechanism | Signed cookie with `itsdangerous.TimestampSigner` | No DB session table; tamper-resistant; standard FastAPI pattern |
| Password storage | Plain text constant `wero123` | Acceptable for single-admin local MVP; documented |
| Cookie name | `wero_admin` | Namespaced to avoid collisions |
| Cookie max-age | 7 days | Long enough to not annoy the admin |
| Cookie flags | `httponly=True, samesite="lax", secure=False (dev)` | Standard security defaults |
| Login form | Plain HTML form (no JS) | Simplest; works without JS |
| Auth middleware | FastAPI `Depends(get_current_admin)` returns string OR RedirectResponse | DRY; one place to enforce auth |
| Banner update | `INSERT ... ON CONFLICT DO UPDATE` | Idempotent; works even if config row deleted |
| Orders viewer | Read-only table, last 50, ordered DESC | No pagination for v1 |
| Logout | `GET /admin/logout` (not POST) | Simpler; no CSRF risk for admin panel |
| Active link highlighting | Server-side via Jinja conditional in base_admin.html | No JS needed |
| Image strategy | Not in scope | Deferred to future change |

## 9. Out of Scope (future changes)

- Real product images, image upload
- Order status updates / fulfillment tracking
- Multi-admin / role-based access
- Email / SMS notifications
- Password reset (bcrypt + user table)
- Analytics / dashboard charts
- Pagination on orders table

## 10. Risks

- **Plain text password**: documented as known limitation; single-admin local MVP
- **SECRET_KEY is hardcoded with a default**: overridable via env var, but operators must remember to set it in production
- **Auth via `return RedirectResponse` from dependency**: works in FastAPI but is a less common pattern; well-tested in the verify phase
- **No CSRF protection on admin POSTs**: `samesite="lax"` cookie provides baseline protection; for production, add CSRF tokens
- **Toggle endpoint is idempotent only for the current state**: calling it twice returns to the original state. This is intentional (toggle semantics).
- **Order total computed with SUM() in SQL**: if there are rounding issues, they accumulate. For an MVP, acceptable.
- **No request rate limiting**: an attacker could brute-force the password. For local MVP, acceptable. For production, add `slowapi` or similar.

## 11. Smoke Test (for sdd-verify)

```bash
# Start uvicorn
rm -f el_perro_wero.db
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8765 > /tmp/uvi.log 2>&1 &
UPID=$!
sleep 3

# 1. GET /admin/login (unauthenticated) returns 200
echo "--- GET /admin/login (unauth) ---"
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/admin/login  # → 200

# 2. GET /admin/ (unauthenticated) redirects to /admin/login
echo "--- GET /admin/ (unauth) ---"
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8765/admin/  # → 303 /admin/login

# 3. POST /admin/login with wrong password returns 200 with error
echo "--- POST /admin/login (wrong) ---"
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8765/admin/login -d "password=wrong"  # → 200

# 4. POST /admin/login with correct password sets cookie and redirects
echo "--- POST /admin/login (correct) ---"
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" -c /tmp/cookies.txt -X POST http://127.0.0.1:8765/admin/login -d "password=wero123"  # → 303 /admin/
cat /tmp/cookies.txt | grep wero_admin  # → wero_admin <token>

# 5. GET /admin/ (authenticated) returns 200
echo "--- GET /admin/ (auth) ---"
curl -fsS -o /dev/null -w "%{http_code}\n" -b /tmp/cookies.txt http://127.0.0.1:8765/admin/  # → 200

# 6. GET /admin/inventario (auth) lists 6 products
echo "--- GET /admin/inventario (auth) ---"
curl -fsS -b /tmp/cookies.txt http://127.0.0.1:8765/admin/inventario | grep -c "card-producto\|admin-table\|producto"  # → ≥ 6

# 7. POST /admin/inventario/JO-001/toggle flips state
echo "--- Toggle JO-001 ---"
sqlite3 el_perro_wero.db "SELECT disponible FROM productos WHERE sku='JO-001';"  # → 1
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" -b /tmp/cookies.txt -X POST http://127.0.0.1:8765/admin/inventario/JO-001/toggle
sqlite3 el_perro_wero.db "SELECT disponible FROM productos WHERE sku='JO-001';"  # → 0

# 8. Home page reflects toggle
echo "--- Home page reflects toggle ---"
curl -fsS http://127.0.0.1:8765/ | grep -c "Agotado"  # → ≥ 1 (JO-001 now sold out)

# 9. GET /admin/banner shows current value
echo "--- GET /admin/banner ---"
curl -fsS -b /tmp/cookies.txt http://127.0.0.1:8765/admin/banner | grep -c "SÚPER PROMO"  # → ≥ 1

# 10. POST /admin/banner updates
echo "--- POST /admin/banner ---"
curl -s -o /dev/null -w "%{http_code}\n" -b /tmp/cookies.txt -X POST http://127.0.0.1:8765/admin/banner -d "banner_text=¡Nueva promo de Wero!"
sqlite3 el_perro_wero.db "SELECT valor FROM configuracion WHERE llave='banner_promocion';"  # → "¡Nueva promo de Wero!"

# 11. Home page shows new banner
echo "--- Home page new banner ---"
curl -fsS http://127.0.0.1:8765/ | grep -c "Nueva promo"  # → ≥ 1

# 12. Place an order via public flow, then check /admin/ordenes
echo "--- Place order, then view admin orders ---"
curl -fsS -X POST http://127.0.0.1:8765/ordenes \
  -H "Content-Type: application/json" \
  -d '{"items":[{"sku":"JO-001","cantidad":1}],"customer":{"nombre":"Admin Test","telefono":"5550000001","edad":30,"genero":"M"}}' > /dev/null
curl -fsS -b /tmp/cookies.txt http://127.0.0.1:8765/admin/ordenes | grep -c "Admin Test"  # → ≥ 1

# 13. GET /admin/logout clears cookie
echo "--- GET /admin/logout ---"
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" -b /tmp/cookies.txt -c /tmp/cookies2.txt http://127.0.0.1:8765/admin/logout
grep -c wero_admin /tmp/cookies2.txt  # → 0 (cookie cleared)

# 14. Static admin.css served
echo "--- admin.css served ---"
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/static/css/admin.css  # → 200

# 15. mypy + ruff
mypy app/ 2>&1 | tail -3
ruff check app/ 2>&1 | tail -3

kill $UPID 2>/dev/null
wait $UPID 2>/dev/null
```

## 12. Dependencies

- `itsdangerous>=2.1` (already in pyproject.toml from change-003)
- `secrets` (stdlib)
- `os` (stdlib)
- No new third-party deps

## Cross-references

- Proposal: `proposal.md` (this change)
- Specs: `specs/{admin-auth,admin-ui}/spec.md`
- Tasks: `tasks.md`
- Umbrella: `../change-002-features/proposal.md`
- Foundation: `../archive/2026-06-07-change-001-foundation/` (has `base_admin.html` skeleton)
- Public UI: `../change-003-public-ui/` and `../change-004-cart-whatsapp/` (admin manages products and config that they created)
