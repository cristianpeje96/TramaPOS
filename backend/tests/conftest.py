"""
TramaPos · Fixtures compartidos de pytest.

Las pruebas corren contra una base de datos PostgreSQL REAL (no SQLite),
porque el schema usa triggers, columnas GENERATED y tipos específicos de
Postgres que SQLite no soporta. Por eso hace falta una base separada,
'tramapos_test', con el mismo schema.sql — nunca corras las pruebas
contra la base de producción/desarrollo (se limpia entre cada prueba).

Setup necesario (una sola vez):
    createdb tramapos_test
    psql -U postgres -d tramapos_test -f ../schema.sql

Variable de entorno opcional para apuntar a otra base de pruebas:
    TEST_DATABASE_URL=postgresql+asyncpg://usuario:pass@localhost:5432/tramapos_test
"""

import asyncio
import os
import sys

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# En Windows, asyncio usa por defecto ProactorEventLoop, que asyncpg no
# soporta bien. Hay que fijar la política ANTES de que cualquier loop
# se cree — por eso va acá, a nivel de módulo.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/tramapos_test",
)

TABLAS_A_LIMPIAR = [
    "devoluciones",
    "detalles_venta",
    "ventas",
    "detalles_compra",
    "compras",
    "historial_puntos",
    "sesiones_caja",
    "clientes",
    "variantes_producto",
    "productos",
    "categorias",
    "proveedores",
    "usuarios",
    "rangos_descuento_fidelizacion",
]


def pytest_collection_modifyitems(items):
    """
    Fuerza a que TODAS las pruebas async compartan un único event loop
    de sesión (en vez de que pytest-asyncio cree uno nuevo por prueba).
    Es la causa raíz de los errores de conexión: una conexión de
    asyncpg abierta en un loop no se puede reusar en otro.
    """
    for item in items:
        item.add_marker(pytest.mark.asyncio(loop_scope="session"))


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _engine():
    """Un solo engine para TODA la sesión de pruebas — se crea una vez."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db(_engine):
    """
    Sesión de base de datos para una prueba individual. Se trunca TODO
    antes de empezar (no después) — así cada prueba arranca desde cero
    sin importar qué haya dejado la anterior.
    """
    async with _engine.begin() as conn:
        tablas = ", ".join(TABLAS_A_LIMPIAR)
        await conn.execute(text(f"TRUNCATE TABLE {tablas} RESTART IDENTITY CASCADE"))

    session_local = async_sessionmaker(bind=_engine, expire_on_commit=False)
    async with session_local() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def caja_fisica_id(db):
    """Las pruebas de caja/ventas necesitan una caja física existente."""
    from sqlalchemy import select

    from app.modules.cajas_fisicas.models import CajaFisica

    resultado = await db.execute(select(CajaFisica).limit(1))
    caja = resultado.scalar_one_or_none()
    if caja is None:
        caja = CajaFisica(nombre="Caja de pruebas")
        db.add(caja)
        await db.commit()
        await db.refresh(caja)
    return caja.id


@pytest_asyncio.fixture(loop_scope="session")
async def usuario_admin(db):
    from app.modules.usuarios.models import RolUsuario
    from app.modules.usuarios.schemas import UsuarioCrear
    from app.modules.usuarios.service import crear_usuario

    return await crear_usuario(
        db,
        UsuarioCrear(
            nombre_completo="Admin de pruebas",
            username="admin_test",
            password="claveSegura123",
            rol=RolUsuario.ADMIN,
        ),
    )


@pytest_asyncio.fixture(loop_scope="session")
async def producto_con_stock(db):
    """Un producto con una variante con 20 unidades de stock, listo para vender."""
    from app.modules.productos.models import Producto, VarianteProducto

    producto = Producto(nombre="Hilo de prueba", unidad_medida="unidad")
    producto.variantes = [
        VarianteProducto(
            sku="TEST-001",
            precio_venta=10000,
            costo_unitario=5000,
            stock_actual=20,
            stock_minimo=5,
        )
    ]
    db.add(producto)
    await db.commit()
    await db.refresh(producto, attribute_names=["variantes"])
    return producto


@pytest_asyncio.fixture(loop_scope="session")
async def cliente_de_prueba(db):
    from app.modules.clientes.models import Cliente

    cliente = Cliente(
        tipo_documento="CC", numero_documento="123456789", nombre_completo="Cliente de Prueba"
    )
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente