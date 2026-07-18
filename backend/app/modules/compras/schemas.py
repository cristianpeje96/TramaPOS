"""
TramaPos · Schemas de compras.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.compras.models import EstadoCompra


class LineaCompraCrear(BaseModel):
    variante_id: int
    cantidad: float = Field(gt=0)
    costo_unitario: float = Field(ge=0)


class CompraCrear(BaseModel):
    proveedor_id: int
    numero_factura_proveedor: str | None = None
    fecha_compra: date | None = None  # si no se manda, usa hoy
    lineas: list[LineaCompraCrear] = Field(min_length=1)
    actualizar_costo_producto: bool = Field(
        default=True,
        description="Si True, el costo_unitario de cada variante se actualiza al de esta compra",
    )


class LineaCompraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    variante_id: int
    cantidad: float
    costo_unitario: float
    producto_nombre: str
    color: str | None = None
    grosor: str | None = None
    sku: str | None = None


class CompraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    proveedor_id: int
    numero_factura_proveedor: str | None
    fecha_compra: date
    subtotal: float
    total: float
    estado: EstadoCompra
    usuario_id: int | None
    creado_en: datetime
    detalles: list[LineaCompraOut] = []


class AnularCompraIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)