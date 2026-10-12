"""Report configuration readiness without displaying credentials."""

import importlib.metadata
import os
import sys
import tempfile

import requests

from config import settings
from prepare_godot import blender_command


def diagnose():
    result = [("Python", sys.version.split()[0])]
    for package in ("gradio", "gradio_client", "requests", "Pillow", "python-dotenv", "filelock"):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "FALTA: instala requirements.txt"
        result.append((package, version))
    for key in ("AGNES_API_KEY", "HF_TOKEN", "STYLIZER_PASSWORD"):
        result.append((key, "configurada" if os.environ.get(key) else "sin configurar"))
    try:
        blender_command()
        result.append(("Blender", "detectado"))
    except (ValueError, RuntimeError):
        result.append(("Blender", "no detectado; necesario solo para preparar Godot"))
    mode = os.environ.get("STYLIZER_PROMPT_MODE", "ollama")
    if mode == "template":
        result.append(("Texto", "plantilla sin Ollama; requiere AGNES_API_KEY para generar la imagen"))
    else:
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat").removesuffix("/api/chat") + "/api/tags"
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            models = [item["name"] for item in response.json().get("models", [])]
            required = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
            result.append(("Ollama", "listo" if required in models else f"descarga el modelo {required}"))
        except (requests.RequestException, ValueError, KeyError):
            result.append(("Ollama", "no disponible; usa una imagen o STYLIZER_PROMPT_MODE=template"))
    cfg = settings()
    for name, folder in (("Datos", cfg.data_dir), ("Resultados", cfg.output_dir)):
        try:
            folder.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=folder) as probe:
                probe.write(b"stylizer")
            result.append((name, "disponible"))
        except OSError:
            result.append((name, "sin acceso de escritura"))
    return result


if __name__ == "__main__":
    for name, status in diagnose():
        print(f"{name}: {status}")
