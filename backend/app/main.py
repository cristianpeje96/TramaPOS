"""
TramaPos · Punto de entrada del backend.
Corre con: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.caja.router import router as caja_router
from app.modules.cajas_fisicas.router import router as cajas_fisicas_router
from app.modules.clientes.router import router as clientes_router
from app.modules.compras.router import router as compras_router
from app.modules.configuracion_empresa.router import router as configuracion_empresa_router
from app.modules.devoluciones.router import router as devoluciones_router
from app.modules.facturacion_dian.router import router as facturacion_dian_router
from app.modules.fidelizacion.router import router as fidelizacion_router
from app.modules.productos.router import router as productos_router
from app.modules.proveedores.router import router as proveedores_router
from app.modules.reportes.router import router as reportes_router
from app.modules.usuarios.router import router_auth, router_usuarios
from app.modules.ventas.router import router as ventas_router
from app.websockets.hub import router as websocket_router

app = FastAPI(
    title=settings.app_nombre,
    description="Backend API-first del sistema POS/ERP de TramaPos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers REST, todos bajo /api/v1 ---
API_PREFIX = "/api/v1"
app.include_router(productos_router, prefix=API_PREFIX)
app.include_router(clientes_router, prefix=API_PREFIX)
app.include_router(fidelizacion_router, prefix=API_PREFIX)
app.include_router(ventas_router, prefix=API_PREFIX)
app.include_router(caja_router, prefix=API_PREFIX)
app.include_router(cajas_fisicas_router, prefix=API_PREFIX)
app.include_router(facturacion_dian_router, prefix=API_PREFIX)
app.include_router(devoluciones_router, prefix=API_PREFIX)
app.include_router(router_auth, prefix=API_PREFIX)
app.include_router(router_usuarios, prefix=API_PREFIX)
app.include_router(configuracion_empresa_router, prefix=API_PREFIX)
app.include_router(proveedores_router, prefix=API_PREFIX)
app.include_router(compras_router, prefix=API_PREFIX)
app.include_router(reportes_router, prefix=API_PREFIX)

# --- WebSocket de sincronización entre terminales POS ---
app.include_router(websocket_router)


@app.get("/health", tags=["sistema"])
async def health_check():
    """Usado por el frontend al arrancar para confirmar que el backend responde."""
    return {"status": "ok", "app": settings.app_nombre, "entorno": settings.env}