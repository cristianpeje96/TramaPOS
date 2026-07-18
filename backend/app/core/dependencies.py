"""
TramaPos · Dependencias de autenticación y roles.

- obtener_usuario_actual: decodifica el JWT del header Authorization,
  y devuelve el Usuario correspondiente. Se usa en CUALQUIER endpoint
  que requiera estar logueado (la gran mayoría).
- requiere_rol(...): fábrica de dependencias para endpoints que además
  necesitan un rol específico (ej. solo ADMIN puede crear productos).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decodificar_access_token
from app.db.session import get_db
from app.modules.usuarios.models import RolUsuario, Usuario

# tokenUrl es solo informativo (para la documentación /docs), el login
# real vive en POST /api/v1/auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


async def obtener_usuario_actual(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    error_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o sesión expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise error_credenciales

    payload = decodificar_access_token(token)
    if payload is None or "sub" not in payload:
        raise error_credenciales

    usuario_id = int(payload["sub"])
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise error_credenciales

    return usuario


def requiere_rol(*roles_permitidos: RolUsuario):
    """
    Uso: Depends(requiere_rol(RolUsuario.ADMIN))
    Reutiliza obtener_usuario_actual (o sea, también exige estar logueado)
    y además valida que el rol del usuario esté en la lista permitida.
    """

    async def verificar(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return usuario

    return verificar