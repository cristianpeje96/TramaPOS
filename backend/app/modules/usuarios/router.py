"""
TramaPos · Router del módulo usuarios.
Dos prefijos montados en main.py:
  - /api/v1/auth      (login, quién soy)
  - /api/v1/usuarios  (administración de cuentas, solo ADMIN)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual, requiere_rol
from app.core.security import crear_access_token
from app.db.session import get_db
from app.modules.usuarios import service
from app.modules.usuarios.models import RolUsuario, Usuario
from app.modules.usuarios.schemas import LoginIn, TokenOut, UsuarioCrear, UsuarioOut

router_auth = APIRouter(prefix="/auth", tags=["auth"])
router_usuarios = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router_auth.post("/login", response_model=TokenOut)
async def login(datos: LoginIn, db: AsyncSession = Depends(get_db)):
    usuario = await service.autenticar_usuario(db, datos.username, datos.password)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = crear_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return TokenOut(access_token=token, usuario=usuario)


@router_auth.get("/me", response_model=UsuarioOut)
async def quien_soy(usuario: Usuario = Depends(obtener_usuario_actual)):
    return usuario


@router_usuarios.get("", response_model=list[UsuarioOut])
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.listar_usuarios(db)


@router_usuarios.post("", response_model=UsuarioOut, status_code=201)
async def crear_usuario(
    datos: UsuarioCrear,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.crear_usuario(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc