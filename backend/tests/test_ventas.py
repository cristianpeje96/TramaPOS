"""
TramaPos · Pruebas del módulo ventas.
Cubre lo más frágil del sistema: la transacción atómica de procesar_venta.
"""

import pytest

from app.modules.fidelizacion.service import registrar_movimiento
from app.modules.fidelizacion.models import TipoMovimientoPuntos
from app.modules.ventas.models import CanalVenta, MetodoPago
from app.modules.ventas.schemas import LineaVentaCrear, VentaCrear
from app.modules.ventas.service import procesar_venta


async def _abrir_sesion_caja(db, caja_fisica_id, usuario_id):
    from app.modules.caja.service import abrir_sesion

    return await abrir_sesion(db, caja_fisica_id, usuario_id, monto_apertura=50000)


@pytest.mark.asyncio
async def test_venta_exitosa_descuenta_stock(db, caja_fisica_id, usuario_admin, producto_con_stock):
    sesion = await _abrir_sesion_caja(db, caja_fisica_id, usuario_admin.id)
    variante = producto_con_stock.variantes[0]

    datos = VentaCrear(
        canal=CanalVenta.POS,
        sesion_caja_id=sesion.id,
        metodo_pago=MetodoPago.EFECTIVO,
        lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=3)],
    )
    venta = await procesar_venta(db, datos, vendedor_id=usuario_admin.id)

    assert venta.subtotal == 30000  # 3 * 10000
    assert venta.total == 30000

    await db.refresh(variante)
    assert variante.stock_actual == 17  # 20 - 3


@pytest.mark.asyncio
async def test_venta_con_stock_insuficiente_falla_y_no_descuenta_nada(
    db, caja_fisica_id, usuario_admin, producto_con_stock
):
    sesion = await _abrir_sesion_caja(db, caja_fisica_id, usuario_admin.id)
    variante = producto_con_stock.variantes[0]

    datos = VentaCrear(
        canal=CanalVenta.POS,
        sesion_caja_id=sesion.id,
        metodo_pago=MetodoPago.EFECTIVO,
        lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=999)],  # más de lo que hay
    )

    with pytest.raises(ValueError, match="Stock insuficiente"):
        await procesar_venta(db, datos, vendedor_id=usuario_admin.id)

    await db.refresh(variante)
    assert variante.stock_actual == 20  # sigue intacto, nada se descontó


@pytest.mark.asyncio
async def test_venta_calcula_puntos_ganados_sobre_el_total(
    db, caja_fisica_id, usuario_admin, producto_con_stock, cliente_de_prueba
):
    sesion = await _abrir_sesion_caja(db, caja_fisica_id, usuario_admin.id)
    variante = producto_con_stock.variantes[0]

    datos = VentaCrear(
        canal=CanalVenta.POS,
        sesion_caja_id=sesion.id,
        cliente_id=cliente_de_prueba.id,
        metodo_pago=MetodoPago.EFECTIVO,
        lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=1)],  # $10.000
    )
    venta = await procesar_venta(db, datos, vendedor_id=usuario_admin.id)

    # 1 punto por cada $1.000 (config por defecto) -> 10 puntos
    assert venta.puntos_ganados == 10

    await db.refresh(cliente_de_prueba)
    assert cliente_de_prueba.puntos_balance == 10
    assert cliente_de_prueba.puntos_totales_historicos == 10


@pytest.mark.asyncio
async def test_venta_con_descuento_manual_porcentaje(
    db, caja_fisica_id, usuario_admin, producto_con_stock
):
    sesion = await _abrir_sesion_caja(db, caja_fisica_id, usuario_admin.id)
    variante = producto_con_stock.variantes[0]

    datos = VentaCrear(
        canal=CanalVenta.POS,
        sesion_caja_id=sesion.id,
        metodo_pago=MetodoPago.EFECTIVO,
        lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=1)],  # $10.000
        descuento_manual_porcentaje=10,
        motivo_descuento_manual="Cliente frecuente",
    )
    venta = await procesar_venta(db, datos, vendedor_id=usuario_admin.id)

    assert venta.subtotal == 10000
    assert venta.descuento_manual == 1000  # 10%
    assert venta.total == 9000


@pytest.mark.asyncio
async def test_redimir_mas_puntos_de_los_disponibles_falla(db, cliente_de_prueba):
    with pytest.raises(ValueError, match="negativo"):
        await registrar_movimiento(
            db,
            cliente_de_prueba,
            TipoMovimientoPuntos.REDIMIDO,
            -999999,  # el cliente no tiene esto
            nota="prueba",
        )