"""
TramaPos · Router de finanzas.
Prefijo montado en main.py como /api/v1/finanzas.
Todo ADMIN — son datos financieros del negocio completo, no algo que
el cajero necesite ver ni tocar.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import requiere_rol
from app.db.session import get_db
from app.modules.finanzas import service
from app.modules.finanzas.schemas import (
    CategoriaFinancieraCrear,
    CategoriaFinancieraOut,
    MovimientoFinancieroCrear,
    MovimientoFinancieroOut,
    PerdidasGananciasOut,
)
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/finanzas", tags=["finanzas"])


@router.get("/categorias", response_model=list[CategoriaFinancieraOut])
async def listar_categorias(
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.listar_categorias_financieras(db)


@router.post("/categorias", response_model=CategoriaFinancieraOut, status_code=201)
async def crear_categoria(
    datos: CategoriaFinancieraCrear,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.crear_categoria_financiera(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/movimientos", response_model=list[MovimientoFinancieroOut])
async def listar_movimientos(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.listar_movimientos(db, fecha_desde, fecha_hasta, categoria_id)


@router.post("/movimientos", response_model=MovimientoFinancieroOut, status_code=201)
async def crear_movimiento(
    datos: MovimientoFinancieroCrear,
    db: AsyncSession = Depends(get_db),
    admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.crear_movimiento(db, datos, usuario_id=admin.id)


@router.delete("/movimientos/{movimiento_id}", status_code=204)
async def eliminar_movimiento(
    movimiento_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        await service.eliminar_movimiento(db, movimiento_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/perdidas-ganancias", response_model=PerdidasGananciasOut)
async def perdidas_ganancias(
    anio: int = Query(default=None, description="Si no se manda, usa el año actual"),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    from datetime import date as date_type

    anio = anio or date_type.today().year
    return await service.generar_perdidas_ganancias(db, anio)