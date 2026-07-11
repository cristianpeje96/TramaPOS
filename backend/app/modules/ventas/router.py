"""
TramaPos · Router del módulo ventas.
Prefijo montado en main.py como /api/v1/ventas.

El envío a la DIAN se dispara como BackgroundTask para no bloquear la
respuesta HTTP (y por lo tanto no bloquear la impresión del ticket en
el frontend, que espera esta respuesta antes de avisarle al agente de
hardware). La función real de envío vive en el módulo facturacion_dian
(siguiente en la lista) — aquí solo se encola.
"""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.ventas import service
from app.modules.ventas.models import CanalVenta
from app.modules.ventas.schemas import VentaCrear, VentaOut

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.get("", response_model=list[VentaOut])
async def listar_ventas(
    canal: CanalVenta | None = Query(default=None),
    sesion_caja_id: int | None = Query(default=None),
    fecha: date | None = Query(default=None, description="Filtra ventas de un día completo"),
    db: AsyncSession = Depends(get_db),
):
    """Historial de ventas — lo usa Administración y el buscador de Devoluciones."""
    return await service.listar_ventas(db, canal=canal, sesion_caja_id=sesion_caja_id, fecha=fecha)


@router.get("/{venta_id}", response_model=VentaOut)
async def obtener_venta(venta_id: int, db: AsyncSession = Depends(get_db)):
    venta = await service.obtener_venta(db, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta


@router.post("", response_model=VentaOut, status_code=201)
async def crear_venta(
    datos: VentaCrear,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        venta = await service.procesar_venta(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Import local para evitar dependencia circular con facturacion_dian.
    from app.modules.facturacion_dian.tasks import enviar_factura_dian
    from app.websockets.hub import notificar_venta_creada

    background_tasks.add_task(enviar_factura_dian, venta.id)
    background_tasks.add_task(notificar_venta_creada, venta.id, venta.canal.value)

    return venta