"""
TramaPos · Router de cotizaciones.
Prefijo montado en main.py como /api/v1/cotizaciones.
Crear/consultar: cualquier usuario logueado (un cajero también cotiza).
Facturar: cualquier usuario logueado con caja abierta (es una venta real).
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import obtener_usuario_actual
from app.db.session import get_db
from app.modules.cotizaciones import service
from app.modules.cotizaciones.models import EstadoCotizacion
from app.modules.cotizaciones.schemas import (
    CambiarEstadoCotizacionIn,
    CotizacionCrear,
    CotizacionOut,
    FacturarCotizacionIn,
)
from app.modules.usuarios.models import Usuario
from app.modules.ventas.schemas import VentaOut

router = APIRouter(prefix="/cotizaciones", tags=["cotizaciones"])


@router.get("", response_model=list[CotizacionOut])
async def listar_cotizaciones(
    estado: EstadoCotizacion | None = None,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    return await service.listar_cotizaciones(db, estado=estado)


@router.get("/{cotizacion_id}", response_model=CotizacionOut)
async def obtener_cotizacion(
    cotizacion_id: int,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    cotizacion = await service.obtener_cotizacion(db, cotizacion_id)
    if cotizacion is None:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return cotizacion


@router.post("", response_model=CotizacionOut, status_code=201)
async def crear_cotizacion(
    datos: CotizacionCrear,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        return await service.crear_cotizacion(db, datos, usuario_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{cotizacion_id}/estado", response_model=CotizacionOut)
async def cambiar_estado(
    cotizacion_id: int,
    datos: CambiarEstadoCotizacionIn,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        return await service.cambiar_estado(db, cotizacion_id, datos.estado)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{cotizacion_id}/facturar", response_model=VentaOut)
async def facturar_cotizacion(
    cotizacion_id: int,
    datos: FacturarCotizacionIn,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        _cotizacion, venta = await service.facturar_cotizacion(
            db, cotizacion_id, datos, usuario_id=usuario.id
        )
        return venta
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{cotizacion_id}/pdf")
async def descargar_pdf(
    cotizacion_id: int,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    cotizacion = await service.obtener_cotizacion(db, cotizacion_id)
    if cotizacion is None:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    pdf_bytes = service.generar_pdf(cotizacion, nombre_empresa=settings.app_nombre)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={cotizacion.numero}.pdf"},
    )