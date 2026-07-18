"""
TramaPos · Router de configuración de empresa.
Prefijo montado en main.py como /api/v1/configuracion-empresa.
GET disponible para cualquier usuario logueado (el POS necesita saber si
debe mostrar IVA en el ticket); PATCH solo ADMIN (prender/apagar el
interruptor es una decisión administrativa/contable).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual, requiere_rol
from app.db.session import get_db
from app.modules.configuracion_empresa import service
from app.modules.configuracion_empresa.schemas import (
    ConfiguracionEmpresaActualizar,
    ConfiguracionEmpresaOut,
)
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/configuracion-empresa", tags=["configuracion_empresa"])


@router.get("", response_model=ConfiguracionEmpresaOut)
async def obtener_configuracion(
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    return await service.obtener_configuracion(db)


@router.patch("", response_model=ConfiguracionEmpresaOut)
async def actualizar_configuracion(
    datos: ConfiguracionEmpresaActualizar,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.actualizar_configuracion(db, datos)