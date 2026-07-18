"""
TramaPos · Schemas de configuración de empresa.
"""

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracionEmpresaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    aplica_iva: bool
    porcentaje_iva_default: float


class ConfiguracionEmpresaActualizar(BaseModel):
    aplica_iva: bool
    porcentaje_iva_default: float = Field(ge=0, le=100)