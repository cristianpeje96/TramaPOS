"""
TramaPos · Lógica de negocio del módulo clientes.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clientes.models import Cliente
from app.modules.clientes.schemas import ClienteCrear, ClienteCrearRapido


async def crear_cliente(db: AsyncSession, datos: ClienteCrear | ClienteCrearRapido) -> Cliente:
    cliente = Cliente(**datos.model_dump())
    db.add(cliente)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("Ya existe un cliente con ese tipo y número de documento") from exc
    await db.refresh(cliente)
    return cliente


async def buscar_por_documento(db: AsyncSession, numero_documento: str) -> Cliente | None:
    """Búsqueda exacta — usada por el atajo F7 cuando se digita el documento completo."""
    query = select(Cliente).where(Cliente.numero_documento == numero_documento)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()


async def buscar_por_nombre(db: AsyncSession, texto: str, limite: int = 10) -> list[Cliente]:
    """Autocompletado por nombre — usa el índice GIN trigram del schema.sql."""
    query = (
        select(Cliente).where(Cliente.nombre_completo.ilike(f"%{texto}%")).limit(limite)
    )
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def obtener_o_crear_rapido(db: AsyncSession, datos: ClienteCrearRapido) -> Cliente:
    """
    Flujo típico de F7 en caja: si el documento ya existe, lo reutiliza;
    si no, lo crea al vuelo sin frenar la venta.
    """
    existente = await buscar_por_documento(db, datos.numero_documento)
    if existente is not None:
        return existente
    return await crear_cliente(db, datos)