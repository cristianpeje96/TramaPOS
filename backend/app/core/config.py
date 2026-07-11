"""
TramaPos · Configuración central del backend.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
    env_file=".env", env_file_encoding="utf-8", extra="ignore"
)

    # --- Entorno ---
    env: str = "development"
    debug: bool = True
    app_nombre: str = "TramaPos"

    # --- Base de datos ---
    database_url: str
    db_pool_size: int = 10

    # --- Seguridad ---
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # --- CORS ---
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",")]

    # --- Fidelización (valores por defecto; la fuente de verdad real
    # vive en la tabla configuracion_fidelizacion, esto es solo fallback) ---
    pesos_por_punto: float = 1000
    valor_punto_redimido: float = 1

    # --- Facturación electrónica DIAN ---
    dian_provider_base_url: str = ""
    dian_provider_api_key: str = ""
    dian_nit_emisor: str = ""
    dian_ambiente: str = "habilitacion"

    # --- Agente de hardware ---
    hardware_agent_ws_url: str = "ws://localhost:9100"


# Instancia única reutilizada en toda la app vía Depends(get_settings)
settings = Settings()


def get_settings() -> Settings:
    return settings
