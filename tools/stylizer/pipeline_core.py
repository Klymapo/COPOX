"""Shared pipeline for the CLI and Gradio, with artifacts per run."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps
from mesh_service import PROVIDERS, reconstruct
from artifacts import package_run
from config import settings, redact

OUTPUT_ROOT = settings().output_dir


def save_run(run):
    path = Path(run["directory"]) / "manifest.json"
    temporary = path.with_name("manifest_" + uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return path


def copy_image(source, destination):
    """Validate a single image and preserve transparency."""
    with Image.open(source) as image:
        if image.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("Usa una imagen PNG, JPEG o WebP.")
        if image.width * image.height > 25_000_000:
            raise ValueError("La imagen supera el límite de 25 megapíxeles.")
        image.load()
        image = ImageOps.exif_transpose(image)
        mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
        normalized = image.convert(mode)
    normalized.save(destination, "PNG")


def run_pipeline(*, idea=None, image_path=None, provider="auto", output_root=OUTPUT_ROOT, progress=None, run_id=None, on_update=None):
    """Return a manifest, preserving partial artifacts when a stage fails."""
    idea = (idea or "").strip()
    if bool(idea) == bool(image_path):
        raise ValueError("Elige una idea o una imagen existente.")
    if provider not in PROVIDERS:
        raise ValueError("Proveedor desconocido.")
    notify = progress or (lambda message: None)
    run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:12]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
        raise ValueError("Identificador de generación inválido.")
    directory = Path(output_root).resolve() / run_id
    directory.mkdir(parents=True, exist_ok=False)
    run = {
        "id": run_id, "directory": str(directory),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "image" if image_path else "text",
        "idea": idea, "prompt": "", "image": None, "model": None,
        "status": "preparing", "error": None, "requested_provider": provider,
        "provider": None, "attempts": [],
    }
    def update(message):
        run["stage"] = message
        run["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_run(run)
        if on_update:
            on_update(dict(run))
        notify(message)

    update("Preparando generación…")
    try:
        image_file = directory / "image.png"
        if image_path:
            update("Preparando tu imagen…")
            copy_image(image_path, image_file)
        else:
            # Image input does not need Ollama, Agnes or their credentials.
            from prompt_stylizer import stylize
            from image_generator_agnes import generate_image_agnes

            update("Estilizando la idea…")
            run["prompt"] = stylize(idea)
            (directory / "prompt.json").write_text(
                json.dumps({"idea": idea, "prompt": run["prompt"]}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            update("Generando la imagen…")
            if not generate_image_agnes(run["prompt"], output_file=str(image_file)):
                raise RuntimeError("No se pudo generar la imagen 2D.")
            copy_image(image_file, image_file)
        run["image"] = str(image_file)
        run["status"] = "reconstructing"
        update("Imagen lista; iniciando reconstrucción…")

        run.update(reconstruct(image_file, directory / "model.glb", provider, update))
        run["status"] = "completed" if run["model"] else "failed"
    except Exception as error:
        run["status"] = "failed"
        run["error"] = redact(error)
    if run.get("error"):
        run["error"] = redact(run["error"])
    run["stage"] = "Completado" if run["status"] == "completed" else "Falló la generación"
    run["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_run(run)
    package_run(run)
    if on_update:
        on_update(dict(run))
    return run
