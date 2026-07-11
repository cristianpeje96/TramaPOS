"""
TramaPos · Schemas Pydantic del módulo devoluciones.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DevolucionCrear(BaseModel):
    venta_id: int
    motivo: str = Field(min_length=3, max_length=255)


class DevolucionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    venta_id: int
    motivo: str
    monto_devuelto: float
    creado_en: datetime