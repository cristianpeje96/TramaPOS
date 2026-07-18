"""
TramaPos · Pruebas del módulo fidelizacion.
"""

import pytest

from app.modules.fidelizacion.models import (
    ConfiguracionFidelizacion,
    RangoDescuentoFidelizacion,
    TipoMovimientoPuntos,
)
from app.modules.fidelizacion.service import (
    calcular_puntos_ganados,
    calcular_valor_descuento,
    crear_rango,
    obtener_rango_para_puntos,
    registrar_movimiento,
)
from app.modules.fidelizacion.schemas import RangoDescuentoCrear


def test_calcular_puntos_ganados_redondea_hacia_abajo():
    config = ConfiguracionFidelizacion(pesos_por_punto=1000)
    # $2.900 -> 2.9 puntos -> debe redondear a 2, no regalar el 0.9 sobrante
    assert calcular_puntos_ganados(2900, config) == 2
    assert calcular_puntos_ganados(1000, config) == 1
    assert calcular_puntos_ganados(999, config) == 0


def test_calcular_valor_descuento():
    config = ConfiguracionFidelizacion(valor_punto_redimido=1)
    assert calcular_valor_descuento(100, config) == 100


@pytest.mark.asyncio
async def test_ganar_puntos_acumula_en_puntos_totales_historicos(db, cliente_de_prueba):
    await registrar_movimiento(
        db, cliente_de_prueba, TipoMovimientoPuntos.GANADO, 50, nota="venta de prueba"
    )
    assert cliente_de_prueba.puntos_balance == 50
    assert cliente_de_prueba.puntos_totales_historicos == 50


@pytest.mark.asyncio
async def test_redimir_puntos_no_afecta_puntos_totales_historicos(db, cliente_de_prueba):
    """
    Clave del diseño: el histórico (usado para el rango Bronce/Plata/Oro)
    NUNCA baja al redimir — solo el saldo disponible.
    """
    await registrar_movimiento(db, cliente_de_prueba, TipoMovimientoPuntos.GANADO, 100, nota="venta")
    await registrar_movimiento(db, cliente_de_prueba, TipoMovimientoPuntos.REDIMIDO, -30, nota="canje")

    assert cliente_de_prueba.puntos_balance == 70
    assert cliente_de_prueba.puntos_totales_historicos == 100  # no bajó


@pytest.mark.asyncio
async def test_obtener_rango_elige_el_mas_alto_que_ya_alcanzo(db):
    await crear_rango(db, RangoDescuentoCrear(nombre="Bronce", puntos_minimo=0, puntos_maximo=99, porcentaje_descuento=0))
    await crear_rango(db, RangoDescuentoCrear(nombre="Plata", puntos_minimo=100, puntos_maximo=299, porcentaje_descuento=5))
    await crear_rango(db, RangoDescuentoCrear(nombre="Oro", puntos_minimo=300, puntos_maximo=None, porcentaje_descuento=10))

    rango_bajo = await obtener_rango_para_puntos(db, 50)
    rango_medio = await obtener_rango_para_puntos(db, 150)
    rango_alto = await obtener_rango_para_puntos(db, 500)

    assert rango_bajo.nombre == "Bronce"
    assert rango_medio.nombre == "Plata"
    assert rango_alto.nombre == "Oro"