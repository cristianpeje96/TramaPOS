"""
TramaPos · Pruebas de stock a través de compras (el trigger simétrico
al de ventas: sube stock en vez de bajarlo).
"""

import pytest
import pytest_asyncio

from app.modules.compras.schemas import CompraCrear, LineaCompraCrear
from app.modules.compras.service import anular_compra, procesar_compra
from app.modules.proveedores.models import Proveedor


@pytest_asyncio.fixture(loop_scope="session")
async def proveedor_de_prueba(db):
    proveedor = Proveedor(nombre_comercial="Proveedor de Prueba")
    db.add(proveedor)
    await db.commit()
    await db.refresh(proveedor)
    return proveedor


@pytest.mark.asyncio
async def test_compra_incrementa_el_stock(db, usuario_admin, producto_con_stock, proveedor_de_prueba):
    variante = producto_con_stock.variantes[0]

    datos = CompraCrear(
        proveedor_id=proveedor_de_prueba.id,
        lineas=[LineaCompraCrear(variante_id=variante.id, cantidad=10, costo_unitario=4500)],
    )
    await procesar_compra(db, datos, usuario_id=usuario_admin.id)

    await db.refresh(variante)
    assert variante.stock_actual == 30  # 20 + 10


@pytest.mark.asyncio
async def test_compra_actualiza_el_costo_del_producto(
    db, usuario_admin, producto_con_stock, proveedor_de_prueba
):
    variante = producto_con_stock.variantes[0]
    assert variante.costo_unitario == 5000  # valor inicial del fixture

    datos = CompraCrear(
        proveedor_id=proveedor_de_prueba.id,
        lineas=[LineaCompraCrear(variante_id=variante.id, cantidad=5, costo_unitario=4200)],
        actualizar_costo_producto=True,
    )
    await procesar_compra(db, datos, usuario_id=usuario_admin.id)

    await db.refresh(variante)
    assert variante.costo_unitario == 4200  # se actualizó al nuevo costo


@pytest.mark.asyncio
async def test_anular_compra_revierte_el_stock(
    db, usuario_admin, producto_con_stock, proveedor_de_prueba
):
    variante = producto_con_stock.variantes[0]

    compra = await procesar_compra(
        db,
        CompraCrear(
            proveedor_id=proveedor_de_prueba.id,
            lineas=[LineaCompraCrear(variante_id=variante.id, cantidad=10, costo_unitario=4500)],
        ),
        usuario_id=usuario_admin.id,
    )
    await db.refresh(variante)
    assert variante.stock_actual == 30

    await anular_compra(db, compra.id, motivo="Se registró por error")

    await db.refresh(variante)
    assert variante.stock_actual == 20  # vuelve al valor original


@pytest.mark.asyncio
async def test_anular_compra_falla_si_el_stock_ya_se_vendio(
    db, usuario_admin, producto_con_stock, proveedor_de_prueba
):
    from app.modules.caja.service import abrir_sesion
    from app.modules.ventas.models import CanalVenta, MetodoPago
    from app.modules.ventas.schemas import LineaVentaCrear, VentaCrear
    from app.modules.ventas.service import procesar_venta
    from app.modules.cajas_fisicas.models import CajaFisica

    variante = producto_con_stock.variantes[0]

    compra = await procesar_compra(
        db,
        CompraCrear(
            proveedor_id=proveedor_de_prueba.id,
            lineas=[LineaCompraCrear(variante_id=variante.id, cantidad=10, costo_unitario=4500)],
        ),
        usuario_id=usuario_admin.id,
    )
    # Stock ahora: 30. Se vende casi todo, dejando menos de lo que la
    # compra había agregado -> no se debe poder anular esa compra.
    caja = CajaFisica(nombre="Caja para venta")
    db.add(caja)
    await db.commit()
    await db.refresh(caja)
    sesion = await abrir_sesion(db, caja.id, usuario_admin.id, monto_apertura=0)

    await procesar_venta(
        db,
        VentaCrear(
            canal=CanalVenta.POS,
            sesion_caja_id=sesion.id,
            metodo_pago=MetodoPago.EFECTIVO,
            lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=25)],  # quedan 5
        ),
        vendedor_id=usuario_admin.id,
    )

    with pytest.raises(ValueError, match="ya bajó"):
        await anular_compra(db, compra.id, motivo="Intento de anular")