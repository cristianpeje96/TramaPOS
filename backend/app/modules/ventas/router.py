"""
TramaPos · Router del módulo ventas.
Prefijo montado en main.py como /api/v1/ventas.
Todos los endpoints requieren estar logueado (cajero o admin) — tanto
cajeros como admins necesitan listar/ver ventas para hacer devoluciones.

El envío a la DIAN se dispara como BackgroundTask para no bloquear la
respuesta HTTP (y por lo tanto no bloquear la impresión del ticket en
el frontend, que espera esta respuesta antes de avisarle al agente de
hardware). La función real de envío vive en el módulo facturacion_dian.
"""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual
from app.db.session import get_db
from app.modules.configuracion_empresa import service as configuracion_empresa_service
from app.modules.usuarios.models import Usuario
from app.modules.ventas import service
from app.modules.ventas.models import CanalVenta
from app.modules.ventas.pdf import generar_factura_pdf
from app.modules.ventas.schemas import VentaCrear, VentaOut

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.get("", response_model=list[VentaOut])
async def listar_ventas(
    canal: CanalVenta | None = Query(default=None),
    sesion_caja_id: int | None = Query(default=None),
    fecha: date | None = Query(default=None, description="Filtra ventas de un día completo"),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    """Historial de ventas — lo usa Administración y el buscador de Devoluciones."""
    return await service.listar_ventas(db, canal=canal, sesion_caja_id=sesion_caja_id, fecha=fecha)


@router.get("/{venta_id}", response_model=VentaOut)
async def obtener_venta(
    venta_id: int,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    venta = await service.obtener_venta(db, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta


@router.post("", response_model=VentaOut, status_code=201)
async def crear_venta(
    datos: VentaCrear,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        venta = await service.procesar_venta(db, datos, vendedor_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Import local para evitar dependencia circular con facturacion_dian.
    from app.modules.facturacion_dian.tasks import enviar_factura_dian
    from app.websockets.hub import notificar_venta_creada

    background_tasks.add_task(enviar_factura_dian, venta.id)
    background_tasks.add_task(notificar_venta_creada, venta.id, venta.canal.value)

    return venta


@router.get("/{venta_id}/factura-pdf")
async def descargar_factura_pdf(
    venta_id: int,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    """Factura formal en hoja carta con membrete — para clientes que
    necesitan un comprobante más formal que la tirilla térmica del POS."""
    venta = await service.obtener_venta(db, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    config_empresa = await configuracion_empresa_service.obtener_configuracion(db)
    pdf_bytes = generar_factura_pdf(venta, config_empresa)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=factura-{venta.id}.pdf"},
    )