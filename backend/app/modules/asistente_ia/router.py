"""
TramaPos · Router del asistente de IA.
Prefijo montado en main.py como /api/v1/asistente-ia.
Solo ADMIN — el asistente ve datos financieros del negocio completo.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import requiere_rol
from app.db.session import get_db
from app.modules.asistente_ia import service
from app.modules.asistente_ia.schemas import PreguntaIn, RespuestaOut
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/asistente-ia", tags=["asistente_ia"])


@router.post("/consultar", response_model=RespuestaOut)
async def consultar(
    datos: PreguntaIn,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    historial = [h.model_dump() for h in datos.historial]
    respuesta = await service.conversar(db, datos.mensaje, historial)
    return RespuestaOut(respuesta=respuesta)