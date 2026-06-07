from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    check_password,
    create_session_token,
    get_current_admin,
    verify_session_token,
)
from app.db import get_db
from app.models import Producto

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    """Render the login form, or redirect to dashboard if already authenticated."""
    token = request.cookies.get("wero_admin")
    if token and verify_session_token(token):
        return RedirectResponse(url="/admin/", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": None}
    )


@router.post("/login")
def login_submit(
    request: Request,
    password: str = Form(...),
):
    """Validate password, set signed cookie, redirect to dashboard."""
    if not check_password(password):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Contraseña incorrecta"},
            status_code=200,
        )
    token = create_session_token()
    response = RedirectResponse(url="/admin/", status_code=303)
    response.set_cookie(
        "wero_admin",
        token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        path="/",
        samesite="lax",
    )
    return response


@router.get("/logout")
def logout():
    """Clear the session cookie and redirect to login."""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("wero_admin", path="/")
    return response


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Admin home with nav cards."""
    admin = get_current_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@router.get("/inventario", response_class=HTMLResponse)
def inventario(
    request: Request,
    updated: str | None = None,
):
    """List all products with their disponible state and toggle buttons."""
    admin = get_current_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM productos ORDER BY categoria, sku"
        ).fetchall()
        productos = [Producto.from_row(r) for r in rows]
    return templates.TemplateResponse(
        "admin/inventario.html",
        {"request": request, "productos": productos, "updated": updated},
    )


@router.post("/inventario/{sku}/toggle")
def toggle_inventario(sku: str, request: Request):
    """Flip disponible (0→1 or 1→0) for the given SKU."""
    admin = get_current_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
        conn.execute(
            "UPDATE productos SET disponible = 1 - disponible WHERE sku = ?",
            (sku,),
        )
        conn.commit()
    return RedirectResponse(
        url=f"/admin/inventario?updated={sku}", status_code=303
    )


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

@router.get("/banner", response_class=HTMLResponse)
def banner_form(
    request: Request,
    updated: int | None = None,
):
    """Render the banner editor form pre-filled with current value."""
    admin = get_current_admin(request)
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
    request: Request,
    banner_text: str = Form(...),
):
    """Update the banner_promocion config value."""
    admin = get_current_admin(request)
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


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.get("/ordenes", response_class=HTMLResponse)
def ordenes(request: Request):
    """List the last 50 orders ordered by newest first."""
    admin = get_current_admin(request)
    if isinstance(admin, RedirectResponse):
        return admin
    with get_db() as conn:
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