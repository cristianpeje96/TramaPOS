"""
TramaPos · Lógica de negocio del módulo devoluciones.

Decisión deliberada: la devolución es SIEMPRE total (anula la venta
completa), nunca parcial por línea. Es la opción que menos margen de
error deja al cajero — buscar la venta, confirmar, listo. Si el negocio
más adelante necesita devoluciones parciales, este es el punto de
partida (agregar detalle_devolucion con cantidades por línea).

Todo pasa en una sola transacción, igual que en ventas/service.py:
reponer stock + revertir puntos + anular la venta + registrar la
devolución, o nada.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.clientes.models import Cliente
from app.modules.devoluciones.models import Devolucion
from app.modules.fidelizacion import service as fidelizacion_service
from app.modules.fidelizacion.models import TipoMovimientoPuntos
from app.modules.productos.models import VarianteProducto
from app.modules.ventas.models import EstadoVenta, Venta


async def anular_venta(db: AsyncSession, venta_id: int, motivo: str) -> Devolucion:
    try:
        query = (
            select(Venta)
            .options(selectinload(Venta.detalles))
            .where(Venta.id == venta_id)
            .with_for_update()
        )
        resultado = await db.execute(query)
        venta = resultado.scalar_one_or_none()

        if venta is None:
            raise ValueError(f"Venta {venta_id} no encontrada")
        if venta.estado == EstadoVenta.ANULADA:
            raise ValueError(f"La venta {venta_id} ya fue anulada anteriormente")

        # --- Reponer stock de cada línea ---
        variante_ids = [d.variante_id for d in venta.detalles]
        if variante_ids:
            query_variantes = (
                select(VarianteProducto)
                .where(VarianteProducto.id.in_(variante_ids))
                .with_for_update()
            )
            resultado_variantes = await db.execute(query_variantes)
            variantes = {v.id: v for v in resultado_variantes.scalars().all()}
            for detalle in venta.detalles:
                variante = variantes.get(detalle.variante_id)
                if variante is not None:
                    variante.stock_actual += detalle.cantidad

        # --- Revertir puntos (si la venta tenía cliente) ---
        if venta.cliente_id is not None:
            query_cliente = (
                select(Cliente).where(Cliente.id == venta.cliente_id).with_for_update()
            )
            resultado_cliente = await db.execute(query_cliente)
            cliente = resultado_cliente.scalar_one_or_none()

            if cliente is not None:
                # Quita los puntos que había ganado con esta venta (nunca
                # deja el saldo en negativo, aunque ya se los haya gastado).
                if venta.puntos_ganados > 0:
                    puntos_a_quitar = min(venta.puntos_ganados, cliente.puntos_balance)
                    if puntos_a_quitar > 0:
                        await fidelizacion_service.registrar_movimiento(
                            db,
                            cliente,
                            TipoMovimientoPuntos.AJUSTE_MANUAL,
                            -puntos_a_quitar,
                            venta_id=venta.id,
                            nota=f"Reversión por devolución de venta #{venta.id}",
                        )

                # Devuelve los puntos que el cliente había redimido en esta venta.
                if venta.puntos_redimidos > 0:
                    await fidelizacion_service.registrar_movimiento(
                        db,
                        cliente,
                        TipoMovimientoPuntos.AJUSTE_MANUAL,
                        venta.puntos_redimidos,
                        venta_id=venta.id,
                        nota=f"Devolución de puntos redimidos — venta #{venta.id}",
                    )

        venta.estado = EstadoVenta.ANULADA

        devolucion = Devolucion(venta_id=venta.id, motivo=motivo, monto_devuelto=venta.total)
        db.add(devolucion)

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    await db.refresh(devolucion)
    return devolucion


async def obtener_por_venta(db: AsyncSession, venta_id: int) -> Devolucion | None:
    query = select(Devolucion).where(Devolucion.venta_id == venta_id)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()