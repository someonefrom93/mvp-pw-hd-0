from datetime import date
import secrets
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.models import Producto
from app.schemas import OrderCreate, OrderResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

WHATSAPP_PHONE_FALLBACK = "525555555555"


def build_whatsapp_url(phone: str, message: str) -> str:
    return f"https://wa.me/{phone}?text={quote(message, safe='')}"


def format_order_message(
    numero_orden: str,
    nombre: str,
    telefono: str,
    items: list,
    price_map: dict | None,
    total: float,
) -> str:
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
            assert price_map is not None
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


@router.get("/")
def home(request: Request) -> HTMLResponse:
    with get_db() as conn:
        productos_rows = conn.execute(
            "SELECT * FROM productos ORDER BY categoria, sku"
        ).fetchall()
        productos = [Producto.from_row(r) for r in productos_rows]
        config_rows = conn.execute(
            "SELECT llave, valor FROM configuracion"
        ).fetchall()
        config = {r["llave"]: r["valor"] for r in config_rows}
    return templates.TemplateResponse(
        "public/home.html",
        {"request": request, "productos": productos, "config": config},
    )


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/ordenes", response_model=OrderResponse)
def create_order(payload: OrderCreate) -> OrderResponse:
    nombre = payload.customer.nombre.strip()
    with get_db() as conn:
        cur = conn.cursor()
        skus = [item.sku for item in payload.items]
        placeholders = ",".join("?" * len(skus))
        found = cur.execute(
            f"SELECT sku, nombre, precio FROM productos WHERE sku IN ({placeholders})",
            skus,
        ).fetchall()
        if len(found) != len(skus):
            raise HTTPException(status_code=404, detail="Uno o más productos no existen")

        cur.execute(
            "INSERT INTO clientes (nombre, telefono, edad, genero) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(telefono) DO UPDATE SET "
            "  nombre=excluded.nombre, edad=excluded.edad, genero=excluded.genero",
            (nombre, payload.customer.telefono, payload.customer.edad, payload.customer.genero),
        )
        cliente_id = cur.execute(
            "SELECT id FROM clientes WHERE telefono = ?", (payload.customer.telefono,)
        ).fetchone()["id"]

        numero_orden = f"ORD-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(3)}"

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

        phone_row = cur.execute(
            "SELECT valor FROM configuracion WHERE llave = 'whatsapp_numero'"
        ).fetchone()
        phone = phone_row["valor"] if phone_row else WHATSAPP_PHONE_FALLBACK
        conn.commit()

    items_dicts = [item.model_dump() for item in payload.items]
    message = format_order_message(
        numero_orden, nombre, payload.customer.telefono, items_dicts, price_map, total
    )
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
    message = format_order_message(
        numero_orden, cliente["nombre"], cliente["telefono"], items, None, total
    )
    return RedirectResponse(url=build_whatsapp_url(phone, message), status_code=302)