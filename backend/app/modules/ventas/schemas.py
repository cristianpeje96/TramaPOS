"""
TramaPos · Schemas Pydantic del módulo ventas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.ventas.models import CanalVenta, EstadoFacturaDian, EstadoVenta, MetodoPago


class LineaVentaCrear(BaseModel):
    variante_id: int
    cantidad: float = Field(gt=0)


class VentaCrear(BaseModel):
    canal: CanalVenta
    sesion_caja_id: int | None = None
    cliente_id: int | None = None
    metodo_pago: MetodoPago
    lineas: list[LineaVentaCrear] = Field(min_length=1)
    puntos_a_redimir: int = Field(default=0, ge=0)
    descuento_manual_porcentaje: float | None = Field(default=None, ge=0, le=100)
    descuento_manual_monto: float | None = Field(default=None, ge=0)
    motivo_descuento_manual: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validar_canal_sesion(self) -> "VentaCrear":
        """Espeja el CHECK constraint de la BD, para fallar rápido con un 422 claro."""
        if self.canal == CanalVenta.POS and self.sesion_caja_id is None:
            raise ValueError("Una venta POS requiere sesion_caja_id")
        if self.canal == CanalVenta.WEB and self.sesion_caja_id is not None:
            raise ValueError("Una venta WEB no debe tener sesion_caja_id")
        if self.puntos_a_redimir > 0 and self.cliente_id is None:
            raise ValueError("Para redimir puntos se requiere cliente_id")
        if self.descuento_manual_porcentaje is not None and self.descuento_manual_monto is not None:
            raise ValueError("Usa descuento_manual_porcentaje O descuento_manual_monto, no ambos")
        tiene_descuento_manual = (
            self.descuento_manual_porcentaje is not None or self.descuento_manual_monto is not None
        )
        if tiene_descuento_manual and not self.motivo_descuento_manual:
            raise ValueError("Un descuento manual requiere indicar el motivo")
        return self


class LineaVentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    variante_id: int
    cantidad: float
    precio_unitario: float
    porcentaje_iva_aplicado: float
    iva_linea: float
    producto_nombre: str
    color: str | None = None
    grosor: str | None = None
    sku: str | None = None


class VentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid_publico: uuid.UUID
    canal: CanalVenta
    cliente_id: int | None
    vendedor_id: int | None
    subtotal: float
    descuento_puntos: float
    descuento_manual: float
    motivo_descuento_manual: str | None
    descuento_fidelizacion: float
    rango_fidelizacion_aplicado: str | None
    total_iva: float
    total: float
    metodo_pago: MetodoPago
    estado: EstadoVenta
    estado_factura_dian: EstadoFacturaDian
    puntos_ganados: int
    puntos_redimidos: int
    creado_en: datetime
    detalles: list[LineaVentaOut] = []