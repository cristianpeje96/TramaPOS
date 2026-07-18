"""
TramaPos · Router de reportes.
Prefijo montado en main.py como /api/v1/reportes.
Solo ADMIN — son estadísticas del negocio, no algo que el cajero necesite.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import requiere_rol
from app.db.session import get_db
from app.modules.reportes import service
from app.modules.reportes.schemas import (
    ProductoMasVendidoReporteOut,
    ResumenReporteOut,
    VentasPorDiaOut,
    VentasPorMesOut,
)
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/resumen", response_model=ResumenReporteOut)
async def resumen(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.obtener_resumen(db, fecha_desde, fecha_hasta)


@router.get("/ventas-por-dia", response_model=list[VentasPorDiaOut])
async def ventas_por_dia(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.ventas_por_dia(db, fecha_desde, fecha_hasta)


@router.get("/ventas-por-mes", response_model=list[VentasPorMesOut])
async def ventas_por_mes(
    meses: int = Query(default=12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.ventas_por_mes(db, meses_atras=meses)


@router.get("/productos-mas-vendidos", response_model=list[ProductoMasVendidoReporteOut])
async def productos_mas_vendidos(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    limite: int = Query(default=15, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.productos_mas_vendidos_reporte(db, fecha_desde, fecha_hasta, limite)