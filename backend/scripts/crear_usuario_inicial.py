"""
TramaPos · Crea el primer usuario administrador.

Necesario correrlo UNA vez después de la migración de usuarios — sin
esto no hay forma de loguearse la primera vez (el endpoint para crear
usuarios exige estar logueado como ADMIN, así que el primero hay que
crearlo por fuera de la API).

Uso (desde backend/, con el venv activado):
    python scripts/crear_usuario_inicial.py
"""

import asyncio
import getpass
import sys

sys.path.insert(0, ".")  # para que encuentre el paquete 'app' corriendo desde backend/

from app.db.session import SessionLocal  # noqa: E402
from app.modules.usuarios.models import RolUsuario  # noqa: E402
from app.modules.usuarios.schemas import UsuarioCrear  # noqa: E402
from app.modules.usuarios.service import crear_usuario  # noqa: E402


async def main():
    print("=== TramaPos · Crear usuario administrador inicial ===\n")
    nombre = input("Nombre completo: ").strip()
    username = input("Username (para iniciar sesión): ").strip()
    password = getpass.getpass("Contraseña: ")
    confirmacion = getpass.getpass("Confirma la contraseña: ")

    if password != confirmacion:
        print("\n❌ Las contraseñas no coinciden. Intenta de nuevo.")
        return
    if len(password) < 6:
        print("\n❌ La contraseña debe tener al menos 6 caracteres.")
        return
    if not nombre or not username:
        print("\n❌ Nombre y username son obligatorios.")
        return

    async with SessionLocal() as db:
        try:
            usuario = await crear_usuario(
                db,
                UsuarioCrear(
                    nombre_completo=nombre,
                    username=username,
                    password=password,
                    rol=RolUsuario.ADMIN,
                ),
            )
            print(
                f"\n✅ Usuario creado: {usuario.nombre_completo} (@{usuario.username}), rol ADMIN"
            )
            print("Ya puedes iniciar sesión en el POS con estas credenciales.")
        except ValueError as exc:
            print(f"\n❌ Error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())