"""
TramaPos · Router del módulo caja.
Prefijo montado en main.py como /api/v1/caja.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.caja import service
from app.modules.caja.schemas import AbrirCajaIn, CerrarCajaIn, PreviewCierreOut, SesionCajaOut

router = APIRouter(prefix="/caja", tags=["caja"])


@router.get("/actual", response_model=SesionCajaOut | None)
async def sesion_actual(db: AsyncSession = Depends(get_db)):
    """
    El frontend consulta esto al arrancar el POS: si viene null,
    debe forzar la pantalla de apertura de caja antes de vender.
    """
    return await service.obtener_sesion_abierta(db)


@router.post("/abrir", response_model=SesionCajaOut, status_code=201)
async def abrir_caja(datos: AbrirCajaIn, db: AsyncSession = Depends(get_db)):
    try:
        return await service.abrir_sesion(db, datos.usuario_apertura_id, datos.monto_apertura)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{sesion_id}/preview-cierre", response_model=PreviewCierreOut)
async def preview_cierre(sesion_id: int, db: AsyncSession = Depends(get_db)):
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
async def cerrar_caja(sesion_id: int, datos: CerrarCajaIn, db: AsyncSession = Depends(get_db)):
    try:
        return await service.cerrar_sesion(
            db, sesion_id, datos.usuario_cierre_id, datos.monto_cierre_real
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc