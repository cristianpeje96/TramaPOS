"""
TramaPos · Router del módulo devoluciones.
Prefijo montado en main.py como /api/v1/devoluciones.
Cualquier usuario logueado puede procesar devoluciones — es parte de
la operación diaria de caja, no una función exclusiva de admin.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual
from app.db.session import get_db
from app.modules.devoluciones import service
from app.modules.devoluciones.schemas import DevolucionCrear, DevolucionOut
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/devoluciones", tags=["devoluciones"])


@router.post("", response_model=DevolucionOut, status_code=201)
async def crear_devolucion(
    datos: DevolucionCrear,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        return await service.anular_venta(db, datos.venta_id, datos.motivo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/venta/{venta_id}", response_model=DevolucionOut | None)
async def devolucion_de_venta(
    venta_id: int,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    """El frontend consulta esto antes de ofrecer el botón de devolución,
    para avisar si esa venta ya fue devuelta antes."""
    return await service.obtener_por_venta(db, venta_id)