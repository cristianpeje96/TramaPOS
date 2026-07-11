"""
TramaPos · Schemas Pydantic del módulo clientes.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClienteBase(BaseModel):
    tipo_documento: str = Field(default="CC", max_length=10)
    numero_documento: str = Field(min_length=3, max_length=30)
    nombre_completo: str = Field(min_length=2, max_length=150)
    email: EmailStr | None = None
    telefono: str | None = None
    direccion: str | None = None


class ClienteCrear(ClienteBase):
    pass


class ClienteCrearRapido(BaseModel):
    """
    Versión mínima para el atajo F7 durante una venta activa:
    no se quiere frenar la fila pidiendo dirección/email en ese momento.
    """

    tipo_documento: str = "CC"
    numero_documento: str = Field(min_length=3, max_length=30)
    nombre_completo: str = Field(min_length=2, max_length=150)


class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    puntos_balance: int
    puntos_totales_historicos: int
    creado_en: datetime