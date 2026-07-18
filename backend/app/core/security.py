"""
TramaPos · Seguridad: hash de contraseñas y JWT.

Nunca se guarda una contraseña en texto plano — solo su hash bcrypt.
El JWT es lo que el frontend manda en cada request (header
Authorization: Bearer <token>) para probar quién es, sin tener que
volver a mandar la contraseña en cada llamada.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_contexto_password = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password: str) -> str:
    return _contexto_password.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return _contexto_password.verify(password, password_hash)


def crear_access_token(datos: dict) -> str:
    expira = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {**datos, "exp": expira}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decodificar_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None