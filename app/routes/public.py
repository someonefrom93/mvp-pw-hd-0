from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.models import Producto

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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