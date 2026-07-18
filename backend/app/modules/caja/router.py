"""
TramaPos · Router del módulo caja.
Prefijo montado en main.py como /api/v1/caja.
Todos los endpoints requieren estar logueado (cajero o admin).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual
from app.db.session import get_db
from app.modules.caja import service
from app.modules.caja.schemas import AbrirCajaIn, CerrarCajaIn, PreviewCierreOut, SesionCajaOut
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/caja", tags=["caja"])


@router.get("/actual", response_model=SesionCajaOut | None)
async def sesion_actual(
    caja_fisica_id: int = Query(..., description="Cuál caja física está usando este terminal"),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    """
    El frontend consulta esto al arrancar el POS, para SU caja física
    específica: si viene null, debe forzar la pantalla de apertura de
    caja antes de vender. Otra caja física puede tener su propia sesión
    abierta al mismo tiempo sin ningún conflicto.
    """
    return await service.obtener_sesion_abierta(db, caja_fisica_id)


@router.get("/abiertas", response_model=list[SesionCajaOut])
async def sesiones_abiertas(
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    """Todas las cajas físicas con sesión abierta ahora mismo (vista general)."""
    return await service.listar_sesiones_abiertas(db)


@router.post("/abrir", response_model=SesionCajaOut, status_code=201)
async def abrir_caja(
    datos: AbrirCajaIn,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        return await service.abrir_sesion(
            db, datos.caja_fisica_id, usuario.id, datos.monto_apertura
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{sesion_id}/preview-cierre", response_model=PreviewCierreOut)
async def preview_cierre(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    """
    Lo que debería haber en el cajón según el sistema — para que el
    cajero cuente la caja física y la compare ANTES de confirmar el
    cierre. No modifica nada.
    """
    try:
        return await service.obtener_preview_cierre(db, sesion_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{sesion_id}/cerrar", response_model=SesionCajaOut)
async def cerrar_caja(
    sesion_id: int,
    datos: CerrarCajaIn,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        return await service.cerrar_sesion(db, sesion_id, usuario.id, datos.monto_cierre_real)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc