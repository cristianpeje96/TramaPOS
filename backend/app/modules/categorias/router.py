"""
TramaPos · Router de categorías.
Prefijo montado en main.py como /api/v1/categorias.
GET: cualquier usuario logueado (se necesita para elegir categoría al
crear un producto, incluso desde alta rápida en el POS).
POST/PATCH: solo ADMIN.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import obtener_usuario_actual, requiere_rol
from app.db.session import get_db
from app.modules.categorias import service
from app.modules.categorias.schemas import CategoriaActualizar, CategoriaCrear, CategoriaOut
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
async def listar_categorias(
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(obtener_usuario_actual),
):
    return await service.listar_categorias(db)


@router.post("", response_model=CategoriaOut, status_code=201)
async def crear_categoria(
    datos: CategoriaCrear,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.crear_categoria(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{categoria_id}", response_model=CategoriaOut)
async def actualizar_categoria(
    categoria_id: int,
    datos: CategoriaActualizar,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.actualizar_categoria(db, categoria_id, datos)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc