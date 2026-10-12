"""Prepare a static GLB using Blender, preserving the source file."""

import argparse
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from mesh_service import validate_glb
from artifacts import package_run
import config  # Loads BLENDER_PATH from .env for CLI use.


def blender_command():
    explicit = os.environ.get("BLENDER_PATH", "").strip().strip('"')
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise ValueError("BLENDER_PATH no apunta a un ejecutable de Blender.")
        return [str(path), "--background", "--factory-startup", "--python-exit-code", "1", "--python"]
    executable = shutil.which("blender")
    if not executable and os.name == "nt":
        candidates = sorted((Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blender Foundation").glob("Blender */blender.exe"))
        executable = str(candidates[-1]) if candidates else None
    if executable:
        return [executable, "--background", "--factory-startup", "--python-exit-code", "1", "--python"]
    if importlib.util.find_spec("bpy"):
        return [sys.executable]
    raise RuntimeError("Instala Blender 4.5 o configura BLENDER_PATH para preparar el modelo para Godot.")


def validate_options(height, yaw, triangle_limit):
    if not math.isfinite(height) or not 0.01 <= height <= 100:
        raise ValueError("La altura debe estar entre 0.01 y 100 metros.")
    if not math.isfinite(yaw) or not -360 <= yaw <= 360:
        raise ValueError("El giro debe estar entre -360 y 360 grados.")
    if isinstance(triangle_limit, bool) or not math.isfinite(triangle_limit) or int(triangle_limit) != triangle_limit or triangle_limit < 0:
        raise ValueError("El límite de triángulos debe ser un entero no negativo; 0 conserva la geometría.")


def prepare_asset(source, *, output_dir=None, height=1.8, yaw=0, triangle_limit=0, progress=None, source_image=None):
    source = Path(source).resolve()
    validate_glb(source)
    validate_options(height, yaw, triangle_limit)
    command = blender_command()
    identifier = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
    directory = Path(output_dir).resolve() if output_dir else source.parent / "godot" / identifier
    directory.mkdir(parents=True, exist_ok=False)
    if progress:
        progress("Preparando escala, orientación y materiales en Blender…")
    script = Path(__file__).resolve().parent / "blender_prepare.py"
    arguments = command + [str(script), "--", "--input", str(source), "--output", str(directory),
                           "--height", str(height), "--yaw", str(yaw), "--triangle-limit", str(int(triangle_limit))]
    with (directory / "blender.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(arguments, stdout=log, stderr=subprocess.STDOUT, timeout=900, check=False)
    if result.returncode:
        detail = (directory / "blender.log").read_text(encoding="utf-8", errors="replace")[-1500:]
        raise RuntimeError(f"Blender no pudo preparar el modelo: {detail}")
    model = directory / "model_godot.glb"
    validate_glb(model)
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    guide = Path(__file__).resolve().parent / "docs" / "GODOT_IMPORT.md"
    shutil.copyfile(guide, directory / guide.name)
    image = None
    if source_image:
        shutil.copyfile(source_image, directory / "image.png")
        image = str(directory / "image.png")
    result = {"id": directory.name, "directory": str(directory), "model": str(model), "report": report,
              "image": image, "prompt": "", "provider": "Blender", "status": "completed", "error": None,
              "source": "godot", "created_at": datetime.now().astimezone().isoformat()}
    (directory / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["archive"] = package_run(result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Prepara un GLB estático para revisar e importar en Godot.")
    parser.add_argument("model")
    parser.add_argument("--height", type=float, default=1.8, help="Altura total en metros")
    parser.add_argument("--yaw", type=float, default=0, help="Giro horizontal en grados")
    parser.add_argument("--triangle-limit", type=int, default=0, help="0 conserva la geometría; otro valor activa reducción aproximada")
    args = parser.parse_args()
    try:
        result = prepare_asset(args.model, height=args.height, yaw=args.yaw, triangle_limit=args.triangle_limit, progress=print)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, str(error) + "\n")
    print(f"Paquete para Godot: {result['archive']}")


if __name__ == "__main__":
    main()
