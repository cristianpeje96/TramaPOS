"""
TramaPos · Router del módulo clientes.
Prefijo montado en main.py como /api/v1/clientes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.clientes import service
from app.modules.clientes.schemas import ClienteCrear, ClienteCrearRapido, ClienteOut

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteOut, status_code=201)
async def crear_cliente(datos: ClienteCrear, db: AsyncSession = Depends(get_db)):
    try:
        return await service.crear_cliente(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/rapido", response_model=ClienteOut, status_code=200)
async def obtener_o_crear_rapido(
    datos: ClienteCrearRapido, db: AsyncSession = Depends(get_db)
):
    """Endpoint específico para el atajo F7 durante una venta activa."""
    return await service.obtener_o_crear_rapido(db, datos)


@router.get("/buscar", response_model=list[ClienteOut])
async def buscar_clientes(
    q: str = Query(min_length=1, description="Nombre o número de documento"),
    db: AsyncSession = Depends(get_db),
):
    por_documento = await service.buscar_por_documento(db, q)
    if por_documento:
        return [por_documento]
    return await service.buscar_por_nombre(db, q)