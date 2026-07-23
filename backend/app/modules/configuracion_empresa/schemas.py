"""
TramaPos · Schemas de configuración de empresa.
"""

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracionEmpresaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    aplica_iva: bool
    porcentaje_iva_default: float
    razon_social: str | None = None
    nit: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None


class ConfiguracionEmpresaActualizar(BaseModel):
    aplica_iva: bool
    porcentaje_iva_default: float = Field(ge=0, le=100)
    razon_social: str | None = None
    nit: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None