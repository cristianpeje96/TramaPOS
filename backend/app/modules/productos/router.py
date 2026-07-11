"""
TramaPos · Router del módulo productos.
Prefijo montado en main.py como /api/v1/productos.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.productos import carga_masiva, service
from app.modules.productos.schemas import (
    ProductoActualizar,
    ProductoCrear,
    ProductoDestacadoOut,
    ProductoOut,
    StockBajoOut,
    VarianteProductoActualizar,
    VarianteProductoOut,
)

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("", response_model=list[ProductoOut])
async def listar_productos(
    incluir_inactivos: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Listado completo — lo usa la pantalla de administración, no el POS."""
    return await service.listar_productos(db, incluir_inactivos=incluir_inactivos)


@router.post("", response_model=ProductoOut, status_code=201)
async def crear_producto(datos: ProductoCrear, db: AsyncSession = Depends(get_db)):
    try:
        return await service.crear_producto(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/buscar", response_model=list[ProductoOut])
async def buscar_productos(
    q: str = Query(min_length=1, description="Texto a buscar, ej: 'Guajira'"),
    db: AsyncSession = Depends(get_db),
):
    """Usado por el buscador del POS (F2) — pensado para autocompletar mientras se escribe."""
    return await service.buscar_productos(db, q)


@router.get("/codigo/{codigo}", response_model=ProductoOut)
async def buscar_por_codigo(codigo: str, db: AsyncSession = Depends(get_db)):
    """Usado por el lector de código de barras en caja."""
    variante = await service.obtener_variante_por_codigo(db, codigo)
    if variante is None:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    return variante.producto


@router.get("/stock-bajo", response_model=list[StockBajoOut])
async def stock_bajo(db: AsyncSession = Depends(get_db)):
    """Alertas de stock mínimo para el dashboard."""
    variantes = await service.listar_stock_bajo(db)
    return [
        StockBajoOut(
            producto=v.producto.nombre,
            sku=v.sku,
            color=v.color,
            grosor=v.grosor,
            stock_actual=v.stock_actual,
            stock_minimo=v.stock_minimo,
        )
        for v in variantes
    ]


@router.get("/favoritos", response_model=list[ProductoDestacadoOut])
async def favoritos(db: AsyncSession = Depends(get_db)):
    """Productos marcados por el cajero — acceso rápido en el POS."""
    variantes = await service.listar_favoritos(db)
    return [
        ProductoDestacadoOut(
            variante_id=v.id,
            producto_nombre=v.producto.nombre,
            color=v.color,
            grosor=v.grosor,
            sku=v.sku,
            precio_venta=v.precio_venta,
            stock_actual=v.stock_actual,
            unidad_medida=v.producto.unidad_medida,
        )
        for v in variantes
    ]


@router.get("/mas-vendidos", response_model=list[ProductoDestacadoOut])
async def mas_vendidos(
    limite: int = Query(default=6, ge=1, le=20),
    dias: int = Query(default=30, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """Top variantes por cantidad vendida en los últimos `dias` días."""
    resultados = await service.listar_mas_vendidos(db, limite=limite, dias=dias)
    return [
        ProductoDestacadoOut(
            variante_id=v.id,
            producto_nombre=v.producto.nombre,
            color=v.color,
            grosor=v.grosor,
            sku=v.sku,
            precio_venta=v.precio_venta,
            stock_actual=v.stock_actual,
            unidad_medida=v.producto.unidad_medida,
            cantidad_vendida=cantidad,
        )
        for v, cantidad in resultados
    ]


@router.patch("/{producto_id}", response_model=ProductoOut)
async def actualizar_producto(
    producto_id: int, datos: ProductoActualizar, db: AsyncSession = Depends(get_db)
):
    try:
        return await service.actualizar_producto(db, producto_id, datos)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/variantes/{variante_id}", response_model=VarianteProductoOut)
async def actualizar_variante(
    variante_id: int, datos: VarianteProductoActualizar, db: AsyncSession = Depends(get_db)
):
    try:
        return await service.actualizar_variante(db, variante_id, datos)
    except ValueError as exc:
        codigo = 404 if "no encontrada" in str(exc) else 409
        raise HTTPException(status_code=codigo, detail=str(exc)) from exc


@router.get("/plantilla")
async def descargar_plantilla():
    """Excel descargable con las columnas esperadas + una fila de ejemplo."""
    contenido = carga_masiva.generar_plantilla()
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_productos_tramapos.xlsx"},
    )


@router.post("/carga-masiva")
async def cargar_masivamente(
    archivo: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """
    Sube el Excel lleno a partir de la plantilla. Agrupa variantes por
    nombre de producto; si el SKU ya existe, esa fila se omite (nunca
    sobreescribe) y queda reportada en 'errores'.
    """
    if not archivo.filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    contenido = await archivo.read()
    return await carga_masiva.procesar_archivo(db, contenido)