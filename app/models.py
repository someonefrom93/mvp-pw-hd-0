"""Typed read-side wrappers for sqlite3.Row."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True, frozen=True)
class Producto:
    id: int
    sku: str
    nombre: str
    descripcion: str
    precio: float
    categoria: Literal["jocho", "hamburguesa"]
    imagen_url: str | None
    disponible: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Producto:
        return cls(
            id=row["id"],
            sku=row["sku"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            precio=row["precio"],
            categoria=row["categoria"],
            imagen_url=row["imagen_url"],
            disponible=bool(row["disponible"]),
        )


@dataclass(slots=True, frozen=True)
class Cliente:
    id: int
    nombre: str
    telefono: str
    edad: int
    genero: Literal["M", "F", "Otro"]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Cliente:
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            telefono=row["telefono"],
            edad=row["edad"],
            genero=row["genero"],
        )


@dataclass(slots=True, frozen=True)
class ConfigKey:
    llave: str
    valor: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ConfigKey:
        return cls(llave=row["llave"], valor=row["valor"])


@dataclass(slots=True, frozen=True)
class OrdenLine:
    id: int
    numero_orden: str
    cliente_id: int
    sku: str
    producto: str
    precio: float
    cantidad: int
    fecha_hora: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> OrdenLine:
        return cls(
            id=row["id"],
            numero_orden=row["numero_orden"],
            cliente_id=row["cliente_id"],
            sku=row["sku"],
            producto=row["producto"],
            precio=row["precio"],
            cantidad=row["cantidad"],
            fecha_hora=row["fecha_hora"],
        )