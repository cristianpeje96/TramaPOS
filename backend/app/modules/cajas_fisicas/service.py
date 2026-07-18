"""
TramaPos · Lógica de cajas físicas.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cajas_fisicas.models import CajaFisica
from app.modules.cajas_fisicas.schemas import CajaFisicaCrear


async def listar_cajas_fisicas(db: AsyncSession, solo_activas: bool = True) -> list[CajaFisica]:
    query = select(CajaFisica).order_by(CajaFisica.nombre)
    if solo_activas:
        query = query.where(CajaFisica.activo.is_(True))
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def crear_caja_fisica(db: AsyncSession, datos: CajaFisicaCrear) -> CajaFisica:
    caja = CajaFisica(nombre=datos.nombre)
    db.add(caja)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError(f"Ya existe una caja física llamada '{datos.nombre}'") from exc
    await db.refresh(caja)
    return caja