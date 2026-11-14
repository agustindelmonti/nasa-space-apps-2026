"""Configuración de la capa de datos (variables de entorno o ``.env``)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataSettings(BaseSettings):
    """Rutas, modo offline y credenciales.

    Las credenciales de Earthdata son ``SecretStr`` para que nunca aparezcan en ``repr``,
    logs ni volcados del modelo. POWER no las necesita.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        frozen=True,
    )

    cache_dir: Path = Field(default=Path("data/cache"), validation_alias="CACHE_DIR")
    fixtures_dir: Path = Field(default=Path("data/fixtures/demo"), validation_alias="FIXTURES_DIR")
    demo_mode: bool = Field(default=False, validation_alias="DEMO_MODE")
    offline: bool = Field(default=False, validation_alias="OFFLINE")
    earthdata_username: str | None = Field(default=None, validation_alias="EARTHDATA_USERNAME")
    earthdata_password: SecretStr | None = Field(
        default=None, validation_alias="EARTHDATA_PASSWORD"
    )
    earthdata_token: SecretStr | None = Field(default=None, validation_alias="EARTHDATA_TOKEN")

    @field_validator("earthdata_username", "earthdata_password", "earthdata_token", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @property
    def network_allowed(self) -> bool:
        """Con ``DEMO_MODE`` u ``OFFLINE`` activos no se abre ninguna conexión."""
        return not (self.demo_mode or self.offline)

    @property
    def read_dirs(self) -> tuple[Path, ...]:
        """Directorios donde buscar caché: primero la caché local, después los fixtures."""
        return (self.cache_dir, self.fixtures_dir)
