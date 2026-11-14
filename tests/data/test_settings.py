"""Settings de la capa de datos: .env.example y secretos fuera de repr."""

from __future__ import annotations

from pydantic import SecretStr

from rastrojo.data.settings import DataSettings
from tests.data.conftest import REPO_ROOT


def test_env_example_loads_with_safe_defaults() -> None:
    cfg = DataSettings(_env_file=REPO_ROOT / ".env.example")  # type: ignore[call-arg]
    assert cfg.demo_mode is False and cfg.offline is False
    assert cfg.network_allowed
    assert cfg.earthdata_password is None and cfg.earthdata_token is None


def test_secrets_not_in_repr() -> None:
    cfg = DataSettings(
        earthdata_username="user",
        earthdata_password=SecretStr("hunter2-secret"),
        earthdata_token=SecretStr("tok-secret"),
    )
    text = repr(cfg) + str(cfg) + str(cfg.model_dump())
    assert "hunter2-secret" not in text
    assert "tok-secret" not in text


def test_demo_mode_blocks_network() -> None:
    assert not DataSettings(demo_mode=True).network_allowed
    assert not DataSettings(offline=True).network_allowed
