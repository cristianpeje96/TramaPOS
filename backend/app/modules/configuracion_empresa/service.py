"""
TramaPos · Lógica de configuración de empresa.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.configuracion_empresa.models import ConfiguracionEmpresa
from app.modules.configuracion_empresa.schemas import ConfiguracionEmpresaActualizar


async def obtener_configuracion(db: AsyncSession) -> ConfiguracionEmpresa:
    query = select(ConfiguracionEmpresa).where(ConfiguracionEmpresa.id == 1)
    resultado = await db.execute(query)
    config = resultado.scalar_one_or_none()
    if config is None:
        config = ConfiguracionEmpresa(id=1)
        db.add(config)
        await db.flush()
    return config


async def actualizar_configuracion(
    db: AsyncSession, datos: ConfiguracionEmpresaActualizar
) -> ConfiguracionEmpresa:
    config = await obtener_configuracion(db)
    config.aplica_iva = datos.aplica_iva
    config.porcentaje_iva_default = datos.porcentaje_iva_default
    await db.commit()
    await db.refresh(config)
    return config