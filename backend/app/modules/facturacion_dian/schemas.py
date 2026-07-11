"""
TramaPos · Schemas Pydantic del módulo facturacion_dian.
"""

from pydantic import BaseModel

from app.modules.ventas.models import EstadoFacturaDian


class EstadoFacturaOut(BaseModel):
    venta_id: int
    estado_factura_dian: EstadoFacturaDian
