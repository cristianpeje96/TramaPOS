"""
TramaPos · Schemas de proveedores.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProveedorBase(BaseModel):
    nombre_comercial: str = Field(min_length=2, max_length=150)
    nit_o_documento: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None


class ProveedorCrear(ProveedorBase):
    pass


class ProveedorActualizar(BaseModel):
    nombre_comercial: str | None = Field(default=None, min_length=2, max_length=150)
    nit_o_documento: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    activo: bool | None = None


class ProveedorOut(ProveedorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activo: bool
    creado_en: datetime