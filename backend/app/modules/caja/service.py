"""
TramaPos · Lógica de negocio del módulo caja.

El arqueo solo cuenta ventas en EFECTIVO: el datáfono y las transferencias
no pasan físicamente por el cajón monedero, así que no hacen parte del
conteo de billetes/monedas al cerrar el turno.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.caja.models import EstadoSesionCaja, SesionCaja
from app.modules.ventas.models import EstadoVenta, MetodoPago, Venta


async def obtener_sesion_abierta(db: AsyncSession) -> SesionCaja | None:
    query = select(SesionCaja).where(SesionCaja.estado == EstadoSesionCaja.ABIERTA)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()


async def abrir_sesion(
    db: AsyncSession, usuario_apertura_id: int, monto_apertura: float
) -> SesionCaja:
    sesion_existente = await obtener_sesion_abierta(db)
    if sesion_existente is not None:
        raise ValueError(
            f"Ya existe una sesión de caja abierta (id={sesion_existente.id}). "
            "Debe cerrarse antes de abrir una nueva."
        )

    sesion = SesionCaja(
        usuario_apertura_id=usuario_apertura_id,
        monto_apertura=monto_apertura,
        estado=EstadoSesionCaja.ABIERTA,
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)
    return sesion


async def calcular_monto_esperado(db: AsyncSession, sesion: SesionCaja) -> float:
    """monto_apertura + total de ventas en efectivo registradas en esta sesión."""
    query = select(func.coalesce(func.sum(Venta.total), 0)).where(
        Venta.sesion_caja_id == sesion.id,
        Venta.metodo_pago == MetodoPago.EFECTIVO,
        Venta.estado == EstadoVenta.COMPLETADA,
    )
    resultado = await db.execute(query)
    total_efectivo = float(resultado.scalar_one())
    return float(sesion.monto_apertura) + total_efectivo


async def obtener_preview_cierre(db: AsyncSession, sesion_id: int) -> dict:
    """
    Lo que el cajero ve ANTES de cerrar: cuánto debería haber en el
    cajón según el sistema, para poder contar la caja física y
    compararla antes de confirmar el cierre (no modifica nada en la BD).
    """
    sesion = await db.get(SesionCaja, sesion_id)
    if sesion is None:
        raise ValueError(f"Sesión de caja {sesion_id} no encontrada")
    if sesion.estado == EstadoSesionCaja.CERRADA:
        raise ValueError("Esta sesión de caja ya está cerrada")

    monto_esperado = await calcular_monto_esperado(db, sesion)
    return {
        "sesion_id": sesion.id,
        "monto_apertura": float(sesion.monto_apertura),
        "monto_cierre_esperado": monto_esperado,
    }


async def cerrar_sesion(
    db: AsyncSession, sesion_id: int, usuario_cierre_id: int, monto_cierre_real: float
) -> SesionCaja:
    sesion = await db.get(SesionCaja, sesion_id)
    if sesion is None:
        raise ValueError(f"Sesión de caja {sesion_id} no encontrada")
    if sesion.estado == EstadoSesionCaja.CERRADA:
        raise ValueError("Esta sesión de caja ya está cerrada")

    sesion.monto_cierre_esperado = await calcular_monto_esperado(db, sesion)
    sesion.monto_cierre_real = monto_cierre_real
    sesion.usuario_cierre_id = usuario_cierre_id
    sesion.estado = EstadoSesionCaja.CERRADA
    sesion.cerrada_en = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(sesion)  # trae 'diferencia' ya calculada por PostgreSQL
    return sesion