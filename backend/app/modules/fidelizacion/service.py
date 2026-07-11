"""
TramaPos · Lógica de negocio del módulo fidelizacion.

Decisión de diseño importante: `registrar_movimiento` NO hace commit.
Esto es intencional — cuando una venta ocurre, ganar/redimir puntos debe
pasar en la MISMA transacción que la venta y el descuento de stock
(si algo falla, todo se revierte junto). El módulo `ventas` es quien
hace el commit final. Solo `ajuste_manual` (fuera de una venta) commitea
directamente, porque ahí sí es una operación aislada.
"""

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clientes.models import Cliente
from app.modules.fidelizacion.models import (
    ConfiguracionFidelizacion,
    HistorialPuntos,
    RangoDescuentoFidelizacion,
    TipoMovimientoPuntos,
)
from app.modules.fidelizacion.schemas import RangoDescuentoActualizar, RangoDescuentoCrear


async def obtener_configuracion(db: AsyncSession) -> ConfiguracionFidelizacion:
    query = select(ConfiguracionFidelizacion).where(ConfiguracionFidelizacion.id == 1)
    resultado = await db.execute(query)
    config = resultado.scalar_one_or_none()
    if config is None:
        # Fallback defensivo: si por alguna razón el singleton no existe aún.
        config = ConfiguracionFidelizacion(id=1)
        db.add(config)
        await db.flush()
    return config


def calcular_puntos_ganados(total_venta: float, config: ConfiguracionFidelizacion) -> int:
    """1 punto por cada `pesos_por_punto` COP, redondeado hacia abajo."""
    if config.pesos_por_punto <= 0:
        return 0
    return math.floor(total_venta / float(config.pesos_por_punto))


def calcular_valor_descuento(puntos: int, config: ConfiguracionFidelizacion) -> float:
    return round(puntos * float(config.valor_punto_redimido), 2)


async def registrar_movimiento(
    db: AsyncSession,
    cliente: Cliente,
    tipo: TipoMovimientoPuntos,
    puntos: int,
    venta_id: int | None = None,
    nota: str | None = None,
) -> HistorialPuntos:
    """
    Aplica el movimiento sobre el balance del cliente (en memoria, dentro de
    la sesión activa) y agrega el registro de auditoría. NO hace commit.
    `puntos` ya debe venir con el signo correcto (positivo=ganado, negativo=redimido).
    """
    nuevo_saldo = cliente.puntos_balance + puntos
    if nuevo_saldo < 0:
        raise ValueError("El movimiento dejaría el saldo de puntos en negativo")

    cliente.puntos_balance = nuevo_saldo
    if tipo == TipoMovimientoPuntos.GANADO:
        cliente.puntos_totales_historicos += puntos

    movimiento = HistorialPuntos(
        cliente_id=cliente.id,
        venta_id=venta_id,
        tipo_movimiento=tipo,
        puntos=puntos,
        saldo_resultante=nuevo_saldo,
        nota=nota,
    )
    db.add(movimiento)
    await db.flush()  # asegura que el registro tenga id sin cerrar la transacción
    return movimiento


async def ganar_puntos(
    db: AsyncSession, cliente: Cliente, total_venta: float, venta_id: int
) -> HistorialPuntos:
    config = await obtener_configuracion(db)
    puntos = calcular_puntos_ganados(total_venta, config)
    return await registrar_movimiento(
        db, cliente, TipoMovimientoPuntos.GANADO, puntos, venta_id=venta_id
    )


async def redimir_puntos(
    db: AsyncSession, cliente: Cliente, puntos_a_redimir: int, venta_id: int
) -> HistorialPuntos:
    if puntos_a_redimir <= 0:
        raise ValueError("puntos_a_redimir debe ser mayor a 0")
    if puntos_a_redimir > cliente.puntos_balance:
        raise ValueError("El cliente no tiene suficientes puntos disponibles")

    return await registrar_movimiento(
        db, cliente, TipoMovimientoPuntos.REDIMIDO, -puntos_a_redimir, venta_id=venta_id
    )


async def ajuste_manual(
    db: AsyncSession, cliente: Cliente, puntos: int, nota: str
) -> HistorialPuntos:
    """Operación administrativa aislada (ej: corregir un error) — sí commitea."""
    movimiento = await registrar_movimiento(
        db, cliente, TipoMovimientoPuntos.AJUSTE_MANUAL, puntos, nota=nota
    )
    await db.commit()
    return movimiento


async def historial_de_cliente(
    db: AsyncSession, cliente_id: int, limite: int = 50
) -> list[HistorialPuntos]:
    query = (
        select(HistorialPuntos)
        .where(HistorialPuntos.cliente_id == cliente_id)
        .order_by(HistorialPuntos.creado_en.desc())
        .limit(limite)
    )
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


# --- Rangos de descuento por fidelización ---
async def listar_rangos(db: AsyncSession) -> list[RangoDescuentoFidelizacion]:
    query = select(RangoDescuentoFidelizacion).order_by(RangoDescuentoFidelizacion.puntos_minimo)
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def crear_rango(
    db: AsyncSession, datos: RangoDescuentoCrear
) -> RangoDescuentoFidelizacion:
    rango = RangoDescuentoFidelizacion(**datos.model_dump())
    db.add(rango)
    await db.commit()
    await db.refresh(rango)
    return rango


async def actualizar_rango(
    db: AsyncSession, rango_id: int, datos: RangoDescuentoActualizar
) -> RangoDescuentoFidelizacion:
    rango = await db.get(RangoDescuentoFidelizacion, rango_id)
    if rango is None:
        raise ValueError(f"Rango {rango_id} no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(rango, campo, valor)
    await db.commit()
    await db.refresh(rango)
    return rango


async def obtener_rango_para_puntos(
    db: AsyncSession, puntos_totales_historicos: int
) -> RangoDescuentoFidelizacion | None:
    """
    El rango aplicable es el de mayor puntos_minimo que el cliente ya
    alcanzó. puntos_maximo=NULL significa "sin techo" (el rango más alto).
    """
    query = (
        select(RangoDescuentoFidelizacion)
        .where(
            RangoDescuentoFidelizacion.activo.is_(True),
            RangoDescuentoFidelizacion.puntos_minimo <= puntos_totales_historicos,
        )
        .order_by(RangoDescuentoFidelizacion.puntos_minimo.desc())
        .limit(1)
    )
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()