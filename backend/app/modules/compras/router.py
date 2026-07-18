"""
TramaPos · Router de compras.
Prefijo montado en main.py como /api/v1/compras.
Solo ADMIN — registrar mercancía/inventario es una tarea administrativa,
no algo que el cajero haga desde el mostrador.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import requiere_rol
from app.db.session import get_db
from app.modules.compras import service
from app.modules.compras.schemas import AnularCompraIn, CompraCrear, CompraOut
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/compras", tags=["compras"])


@router.get("", response_model=list[CompraOut])
async def listar_compras(
    proveedor_id: int | None = Query(default=None),
    fecha: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.listar_compras(db, proveedor_id=proveedor_id, fecha=fecha)


@router.get("/{compra_id}", response_model=CompraOut)
async def obtener_compra(
    compra_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    compra = await service.obtener_compra(db, compra_id)
    if compra is None:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return compra


@router.post("", response_model=CompraOut, status_code=201)
async def crear_compra(
    datos: CompraCrear,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.procesar_compra(db, datos, usuario_id=admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{compra_id}/anular", response_model=CompraOut)
async def anular_compra(
    compra_id: int,
    datos: AnularCompraIn,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.anular_compra(db, compra_id, datos.motivo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc