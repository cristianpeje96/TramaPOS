"""
TramaPos · Router del módulo fidelizacion.
Prefijo montado en main.py como /api/v1/fidelizacion.

Nota: NO expone un endpoint de "redimir puntos" aislado — la redención
solo ocurre dentro de POST /ventas (canal=POS, F9 en el frontend), porque
tiene que ir atada a una venta real. Aquí solo van configuración, consulta
de historial, simulación (para pintar el descuento en el POS) y ajustes
manuales administrativos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.clientes.service import buscar_por_documento
from app.modules.fidelizacion import service
from app.modules.fidelizacion.schemas import (
    AjusteManualCrear,
    ConfiguracionFidelizacionActualizar,
    ConfiguracionFidelizacionOut,
    HistorialPuntosOut,
    RangoClienteOut,
    RangoDescuentoActualizar,
    RangoDescuentoCrear,
    RangoDescuentoOut,
    SimulacionRedencionOut,
)
from sqlalchemy import select
from app.modules.clientes.models import Cliente

router = APIRouter(prefix="/fidelizacion", tags=["fidelizacion"])


async def _obtener_cliente_o_404(db: AsyncSession, cliente_id: int) -> Cliente:
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = resultado.scalar_one_or_none()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/configuracion", response_model=ConfiguracionFidelizacionOut)
async def obtener_configuracion(db: AsyncSession = Depends(get_db)):
    return await service.obtener_configuracion(db)


@router.patch("/configuracion", response_model=ConfiguracionFidelizacionOut)
async def actualizar_configuracion(
    datos: ConfiguracionFidelizacionActualizar, db: AsyncSession = Depends(get_db)
):
    config = await service.obtener_configuracion(db)
    config.pesos_por_punto = datos.pesos_por_punto
    config.valor_punto_redimido = datos.valor_punto_redimido
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/historial/{cliente_id}", response_model=list[HistorialPuntosOut])
async def historial_de_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    await _obtener_cliente_o_404(db, cliente_id)
    return await service.historial_de_cliente(db, cliente_id)


@router.get("/simular-redencion/{cliente_id}", response_model=SimulacionRedencionOut)
async def simular_redencion(
    cliente_id: int,
    puntos: int = Query(gt=0, description="Puntos que el cajero quiere redimir (F9)"),
    db: AsyncSession = Depends(get_db),
):
    """
    El frontend llama esto al escribir un número en el input de redención (F9),
    para mostrar el descuento ANTES de confirmar la venta con F10.
    """
    cliente = await _obtener_cliente_o_404(db, cliente_id)
    if puntos > cliente.puntos_balance:
        raise HTTPException(status_code=400, detail="El cliente no tiene suficientes puntos")

    config = await service.obtener_configuracion(db)
    return SimulacionRedencionOut(
        puntos_disponibles=cliente.puntos_balance,
        puntos_a_redimir=puntos,
        valor_descuento=service.calcular_valor_descuento(puntos, config),
    )


@router.post("/ajuste-manual", response_model=HistorialPuntosOut, status_code=201)
async def crear_ajuste_manual(datos: AjusteManualCrear, db: AsyncSession = Depends(get_db)):
    cliente = await _obtener_cliente_o_404(db, datos.cliente_id)
    try:
        return await service.ajuste_manual(db, cliente, datos.puntos, datos.nota)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- Rangos de descuento por fidelización ---
@router.get("/rangos", response_model=list[RangoDescuentoOut])
async def listar_rangos(db: AsyncSession = Depends(get_db)):
    return await service.listar_rangos(db)


@router.post("/rangos", response_model=RangoDescuentoOut, status_code=201)
async def crear_rango(datos: RangoDescuentoCrear, db: AsyncSession = Depends(get_db)):
    return await service.crear_rango(db, datos)


@router.patch("/rangos/{rango_id}", response_model=RangoDescuentoOut)
async def actualizar_rango(
    rango_id: int, datos: RangoDescuentoActualizar, db: AsyncSession = Depends(get_db)
):
    try:
        return await service.actualizar_rango(db, rango_id, datos)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rango-cliente/{cliente_id}", response_model=RangoClienteOut)
async def rango_del_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """El CheckoutPanel llama esto al seleccionar un cliente (F7), para
    mostrar de una vez su descuento automático por nivel de fidelización."""
    cliente = await _obtener_cliente_o_404(db, cliente_id)
    rango = await service.obtener_rango_para_puntos(db, cliente.puntos_totales_historicos)
    return RangoClienteOut(
        rango=rango.nombre if rango else None,
        porcentaje_descuento=float(rango.porcentaje_descuento) if rango else 0,
        puntos_totales_historicos=cliente.puntos_totales_historicos,
    )