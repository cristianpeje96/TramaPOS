"""
TramaPos · Router de proveedores.
Prefijo montado en main.py como /api/v1/proveedores.
Solo ADMIN gestiona proveedores — es administración de datos maestros.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import requiere_rol
from app.db.session import get_db
from app.modules.proveedores import service
from app.modules.proveedores.schemas import ProveedorActualizar, ProveedorCrear, ProveedorOut
from app.modules.usuarios.models import RolUsuario, Usuario

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.get("", response_model=list[ProveedorOut])
async def listar_proveedores(
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.listar_proveedores(db)


@router.get("/buscar", response_model=list[ProveedorOut])
async def buscar_proveedores(
    q: str = Query(min_length=1),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    """Usado por el formulario de nueva compra, para elegir el proveedor."""
    return await service.buscar_proveedores(db, q)


@router.post("", response_model=ProveedorOut, status_code=201)
async def crear_proveedor(
    datos: ProveedorCrear,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    return await service.crear_proveedor(db, datos)


@router.patch("/{proveedor_id}", response_model=ProveedorOut)
async def actualizar_proveedor(
    proveedor_id: int,
    datos: ProveedorActualizar,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(requiere_rol(RolUsuario.ADMIN)),
):
    try:
        return await service.actualizar_proveedor(db, proveedor_id, datos)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc