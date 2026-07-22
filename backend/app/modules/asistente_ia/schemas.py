"""
TramaPos · Schemas del asistente de IA.
"""

from pydantic import BaseModel, Field


class MensajeChat(BaseModel):
    rol: str  # "user" | "assistant"
    contenido: str


class PreguntaIn(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000)
    historial: list[MensajeChat] = Field(default_factory=list, max_length=20)


class RespuestaOut(BaseModel):
    respuesta: str