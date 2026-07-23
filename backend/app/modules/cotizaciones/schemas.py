"""
TramaPos · Schemas de cotizaciones.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.cotizaciones.models import EstadoCotizacion
from app.modules.ventas.models import MetodoPago


class LineaCotizacionCrear(BaseModel):
    variante_id: int
    cantidad: float = Field(gt=0)
    precio_unitario: float | None = Field(
        default=None, description="Si no se manda, usa el precio_venta actual del producto"
    )


class CotizacionCrear(BaseModel):
    cliente_id: int | None = None
    cliente_nombre: str | None = Field(default=None, max_length=150)
    cliente_telefono: str | None = None
    cliente_email: str | None = None
    fecha_vencimiento: date | None = None
    notas: str | None = None
    descuento_manual: float = Field(default=0, ge=0)
    lineas: list[LineaCotizacionCrear] = Field(min_length=1)


class CambiarEstadoCotizacionIn(BaseModel):
    estado: EstadoCotizacion


class FacturarCotizacionIn(BaseModel):
    sesion_caja_id: int
    metodo_pago: MetodoPago


class LineaCotizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    variante_id: int
    cantidad: float
    precio_unitario: float
    producto_nombre: str
    color: str | None = None
    grosor: str | None = None
    sku: str | None = None


class CotizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: str
    cliente_id: int | None
    cliente_nombre: str | None
    cliente_telefono: str | None
    cliente_email: str | None
    fecha_emision: date
    fecha_vencimiento: date | None
    estado: EstadoCotizacion
    subtotal: float
    descuento_manual: float
    total: float
    notas: str | None
    venta_id: int | None
    creado_en: datetime
    detalles: list[LineaCotizacionOut] = []