"""
TramaPos · Pruebas del módulo caja — apertura/cierre y múltiples cajas físicas.
"""

import pytest

from app.modules.caja.service import abrir_sesion, cerrar_sesion
from app.modules.cajas_fisicas.models import CajaFisica
from app.modules.ventas.models import CanalVenta, MetodoPago
from app.modules.ventas.schemas import LineaVentaCrear, VentaCrear
from app.modules.ventas.service import procesar_venta


@pytest.mark.asyncio
async def test_no_se_puede_abrir_dos_sesiones_en_la_misma_caja_fisica(
    db, caja_fisica_id, usuario_admin
):
    await abrir_sesion(db, caja_fisica_id, usuario_admin.id, monto_apertura=20000)

    with pytest.raises(ValueError, match="ya tiene una sesión abierta"):
        await abrir_sesion(db, caja_fisica_id, usuario_admin.id, monto_apertura=20000)


@pytest.mark.asyncio
async def test_dos_cajas_fisicas_distintas_pueden_operar_simultaneamente(db, usuario_admin):
    caja1 = CajaFisica(nombre="Caja 1 prueba")
    caja2 = CajaFisica(nombre="Caja 2 prueba")
    db.add_all([caja1, caja2])
    await db.commit()
    await db.refresh(caja1)
    await db.refresh(caja2)

    sesion1 = await abrir_sesion(db, caja1.id, usuario_admin.id, monto_apertura=10000)
    sesion2 = await abrir_sesion(db, caja2.id, usuario_admin.id, monto_apertura=15000)

    assert sesion1.id != sesion2.id
    assert sesion1.caja_fisica_id == caja1.id
    assert sesion2.caja_fisica_id == caja2.id


@pytest.mark.asyncio
async def test_cierre_de_caja_solo_cuenta_ventas_en_efectivo(
    db, caja_fisica_id, usuario_admin, producto_con_stock
):
    sesion = await abrir_sesion(db, caja_fisica_id, usuario_admin.id, monto_apertura=50000)
    variante = producto_con_stock.variantes[0]  # $10.000 c/u

    # Una venta en efectivo y una en datáfono
    await procesar_venta(
        db,
        VentaCrear(
            canal=CanalVenta.POS,
            sesion_caja_id=sesion.id,
            metodo_pago=MetodoPago.EFECTIVO,
            lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=1)],
        ),
        vendedor_id=usuario_admin.id,
    )
    await procesar_venta(
        db,
        VentaCrear(
            canal=CanalVenta.POS,
            sesion_caja_id=sesion.id,
            metodo_pago=MetodoPago.DATAFONO,
            lineas=[LineaVentaCrear(variante_id=variante.id, cantidad=1)],
        ),
        vendedor_id=usuario_admin.id,
    )

    sesion_cerrada = await cerrar_sesion(db, sesion.id, usuario_admin.id, monto_cierre_real=60000)

    # 50.000 apertura + 10.000 en efectivo (NO se suma el pago con datáfono)
    assert sesion_cerrada.monto_cierre_esperado == 60000
    assert sesion_cerrada.diferencia == 0