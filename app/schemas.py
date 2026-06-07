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


class AdminLogin(BaseModel):
    password: str = Field(..., min_length=1, max_length=200)


class BannerUpdate(BaseModel):
    banner_text: str = Field(..., min_length=1, max_length=500)