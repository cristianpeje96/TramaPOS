"""
TramaPos · Schemas de cajas físicas.
"""

from pydantic import BaseModel, ConfigDict, Field


class CajaFisicaCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=50)


class CajaFisicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    activo: bool