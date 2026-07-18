"""
TramaPos · Schemas del módulo reportes.
"""

from datetime import date

from pydantic import BaseModel


class VentasPorDiaOut(BaseModel):
    fecha: date
    total: float
    cantidad_ventas: int


class VentasPorMesOut(BaseModel):
    anio: int
    mes: int
    total: float
    cantidad_ventas: int


class ProductoMasVendidoReporteOut(BaseModel):
    variante_id: int
    producto_nombre: str
    color: str | None
    grosor: str | None
    sku: str
    cantidad_vendida: float
    total_vendido: float


class ResumenReporteOut(BaseModel):
    total_ventas: float
    cantidad_ventas: int
    ticket_promedio: float