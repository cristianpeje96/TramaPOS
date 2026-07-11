"""
TramaPos · Base declarativa de SQLAlchemy.
Todos los modelos de app/modules/*/models.py heredan de esta Base,
para que Alembic pueda detectarlos y generar migraciones automáticas.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
