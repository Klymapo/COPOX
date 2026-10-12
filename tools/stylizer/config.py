"""Central configuration. Environment variables override the local .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)


def configured_path(name, fallback):
    path = Path(os.environ.get(name) or fallback).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    output_dir: Path
    port: int
    username: str
    password: str


def settings():
    port = int(os.environ.get("STYLIZER_PORT") or os.environ.get("PORT") or "7860")
    if not 1 <= port <= 65535:
        raise ValueError("STYLIZER_PORT debe estar entre 1 y 65535.")
    return Settings(configured_path("STYLIZER_DATA_DIR", ".stylizer"),
                    configured_path("STYLIZER_OUTPUT_DIR", "outputs"), port,
                    os.environ.get("STYLIZER_USER", "atatoriz"), os.environ.get("STYLIZER_PASSWORD", ""))


def validate_server_config(cfg):
    """Fail closed before exposing the application on a hosting provider."""
    if not cfg.username.strip() or len(cfg.password) < 12:
        raise ValueError("Configura STYLIZER_USER y STYLIZER_PASSWORD (mínimo 12 caracteres) para iniciar el servidor.")
    if cfg.data_dir == cfg.output_dir or cfg.data_dir in cfg.output_dir.parents or cfg.output_dir in cfg.data_dir.parents:
        raise ValueError("STYLIZER_DATA_DIR y STYLIZER_OUTPUT_DIR deben ser carpetas separadas, sin contenerse entre sí.")


def redact(message):
    text = str(message)
    for name in ("AGNES_API_KEY", "HF_TOKEN", "STYLIZER_PASSWORD"):
        value = os.environ.get(name)
        if value:
            text = text.replace(value, "[oculto]")
    return text
