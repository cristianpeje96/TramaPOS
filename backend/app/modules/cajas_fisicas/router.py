"""
TramaPos · Router de cajas físicas.
Prefijo montado en main.py como /api/v1/cajas-fisicas.
GET: cualquier usuario logueado (el POS lo necesita al abrir caja).
POST: solo ADMIN (crear una registradora nueva es una decisión administrativa).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual, requiere_rol
from app.db.session import get_db
from app.modules.cajas_fisicas import service
from app.modules.cajas_fisicas.schemas import CajaFisicaCrear, CajaFisicaOut
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/cajas-fisicas", tags=["cajas_fisicas"])


@router.get("", response_model=list[CajaFisicaOut])
async def listar_cajas_fisicas(
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    return await service.listar_cajas_fisicas(db)


@router.post("", response_model=CajaFisicaOut, status_code=201)
async def crear_caja_fisica(
    datos: CajaFisicaCrear,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.crear_caja_fisica(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc