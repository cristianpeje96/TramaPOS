"""
TramaPos · Pruebas del módulo devoluciones.
"""

import pytest

from app.modules.caja.service import abrir_sesion
from app.modules.devoluciones.service import anular_venta
from app.modules.ventas.models import CanalVenta, MetodoPago
from app.modules.ventas.schemas import LineaVentaCrear, VentaCrear
from app.modules.ventas.service import procesar_venta


@pytest.mark.asyncio
async def test_anular_venta_repone_el_stock(
    db, caja_fisica_id, usuario_admin, producto_con_stock
):
    sesion = await abrir_sesion(db, caja_fisica_id, usuario_admin.id, monto_apertura=0)
    variante = producto_con_stock.variantes[0]

    venta = await procesar_venta(
        db,
        VentaCrear(
            canal=CanalVenta.POS,
            sesion_caja_id=sesion.id,
            metodo_pago=MetodoPago.EFECTIVO,
            lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=5)],
        ),
        vendedor_id=usuario_admin.id,
    )
    await db.refresh(variante)
    assert variante.stock_actual == 15  # 20 - 5

    await anular_venta(db, venta.id, motivo="Producto defectuoso")

    await db.refresh(variante)
    assert variante.stock_actual == 20  # repuesto por completo


@pytest.mark.asyncio
async def test_no_se_puede_devolver_la_misma_venta_dos_veces(
    db, caja_fisica_id, usuario_admin, producto_con_stock
):
    sesion = await abrir_sesion(db, caja_fisica_id, usuario_admin.id, monto_apertura=0)
    variante = producto_con_stock.variantes[0]

    venta = await procesar_venta(
        db,
        VentaCrear(
            canal=CanalVenta.POS,
            sesion_caja_id=sesion.id,
            metodo_pago=MetodoPago.EFECTIVO,
            lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=1)],
        ),
        vendedor_id=usuario_admin.id,
    )

    await anular_venta(db, venta.id, motivo="Primera devolución")

    with pytest.raises(ValueError, match="ya fue anulada"):
        await anular_venta(db, venta.id, motivo="Segundo intento")


@pytest.mark.asyncio
async def test_anular_venta_revierte_puntos_ganados(
    db, caja_fisica_id, usuario_admin, producto_con_stock, cliente_de_prueba
):
    sesion = await abrir_sesion(db, caja_fisica_id, usuario_admin.id, monto_apertura=0)
    variante = producto_con_stock.variantes[0]  # $10.000 -> 10 puntos

    venta = await procesar_venta(
        db,
        VentaCrear(
            canal=CanalVenta.POS,
            sesion_caja_id=sesion.id,
            cliente_id=cliente_de_prueba.id,
            metodo_pago=MetodoPago.EFECTIVO,
            lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=1)],
        ),
        vendedor_id=usuario_admin.id,
    )
    await db.refresh(cliente_de_prueba)
    assert cliente_de_prueba.puntos_balance == 10

    await anular_venta(db, venta.id, motivo="Cliente se arrepintió")

    await db.refresh(cliente_de_prueba)
    assert cliente_de_prueba.puntos_balance == 0