"""
TramaPos · Router del módulo facturacion_dian.
Prefijo montado en main.py como /api/v1/facturacion-dian.
Solo ADMIN — es un panel de administración, no algo que el cajero use.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import requiere_rol
from app.db.session import get_db
from app.modules.facturacion_dian.schemas import EstadoFacturaOut
from app.modules.facturacion_dian.tasks import reintentar_factura_dian
from app.modules.usuarios.models import RolUsuario, Usuario
from app.modules.ventas.models import Venta

router = APIRouter(prefix="/facturacion-dian", tags=["facturacion_dian"])


@router.get("/ventas/{venta_id}/estado", response_model=EstadoFacturaOut)
async def estado_factura(
    venta_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    venta = await db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return EstadoFacturaOut(venta_id=venta.id, estado_factura_dian=venta.estado_factura_dian)


@router.post("/ventas/{venta_id}/reintentar", status_code=202)
async def reintentar_factura(
    venta_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    """Botón manual en el dashboard admin para facturas que quedaron RECHAZADA."""
    venta = await db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    background_tasks.add_task(reintentar_factura_dian, venta_id)
    return {"mensaje": f"Reintento de factura encolado para venta {venta_id}"}