"""
TramaPos · Schemas Pydantic del módulo usuarios.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.usuarios.models import RolUsuario


class UsuarioCrear(BaseModel):
    nombre_completo: str = Field(min_length=2, max_length=150)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    rol: RolUsuario = RolUsuario.CAJERO


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_completo: str
    username: str
    rol: RolUsuario
    activo: bool
    creado_en: datetime


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut