"""
TramaPos · Schemas de categorías.
"""

from pydantic import BaseModel, ConfigDict, Field


class CategoriaCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    categoria_padre_id: int | None = None


class CategoriaActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    categoria_padre_id: int | None = None
    activo: bool | None = None


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    categoria_padre_id: int | None
    activo: bool