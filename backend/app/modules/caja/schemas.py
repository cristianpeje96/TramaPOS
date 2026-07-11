"""
TramaPos · Schemas Pydantic del módulo caja.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.caja.models import EstadoSesionCaja


class AbrirCajaIn(BaseModel):
    usuario_apertura_id: int
    monto_apertura: float = Field(ge=0)


class CerrarCajaIn(BaseModel):
    usuario_cierre_id: int
    monto_cierre_real: float = Field(ge=0)


class SesionCajaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_apertura_id: int
    usuario_cierre_id: int | None
    monto_apertura: float
    monto_cierre_esperado: float | None
    monto_cierre_real: float | None
    diferencia: float | None
    estado: EstadoSesionCaja
    abierta_en: datetime
    cerrada_en: datetime | None


class PreviewCierreOut(BaseModel):
    sesion_id: int
    monto_apertura: float
    monto_cierre_esperado: float