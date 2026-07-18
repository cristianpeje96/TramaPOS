"""
TramaPos · Lógica de negocio del módulo usuarios.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hashear_password, verificar_password
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UsuarioCrear


async def crear_usuario(db: AsyncSession, datos: UsuarioCrear) -> Usuario:
    usuario = Usuario(
        nombre_completo=datos.nombre_completo,
        username=datos.username,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
    )
    db.add(usuario)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError(f"El username '{datos.username}' ya está en uso") from exc
    await db.refresh(usuario)
    return usuario


async def autenticar_usuario(db: AsyncSession, username: str, password: str) -> Usuario | None:
    query = select(Usuario).where(Usuario.username == username, Usuario.activo.is_(True))
    resultado = await db.execute(query)
    usuario = resultado.scalar_one_or_none()

    if usuario is None or not verificar_password(password, usuario.password_hash):
        return None
    return usuario


async def listar_usuarios(db: AsyncSession) -> list[Usuario]:
    query = select(Usuario).where(Usuario.activo.is_(True)).order_by(Usuario.nombre_completo)
    resultado = await db.execute(query)
    return list(resultado.scalars().all())