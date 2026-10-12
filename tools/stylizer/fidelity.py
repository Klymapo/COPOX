"""Manual visual review tied to a model and immutable reference snapshots."""

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from artifacts import package_run
from pipeline_core import copy_image, save_run

ASPECTS = ["Silueta y proporciones", "Cara y cabello", "Ropa y accesorios", "Colores y materiales", "Perfil y espalda"]
RATINGS = ["Sin evaluar", "Coincide", "Corregir"]
VIEWS = {"front": "Frente", "side": "Perfil", "back": "Espalda"}


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def correction_plan(ratings, notes):
    lines = []
    for status, heading in [("Coincide", "Conservar"), ("Corregir", "Corregir"), ("Sin evaluar", "Pendiente de evaluar")]:
        names = [aspect for aspect in ASPECTS if ratings[aspect] == status]
        lines.append(f"{heading}: {', '.join(names) if names else 'ninguno marcado'}.")
    if notes.strip():
        lines.append("Indicaciones: " + notes.strip())
    return "\n".join(lines)


def save_review(run, references, ratings, notes=""):
    if not run or not run.get("model") or not Path(run["model"]).is_file():
        raise ValueError("Primero completa una generación 3D para revisarla.")
    if set(ratings) != set(ASPECTS) or any(value not in RATINGS for value in ratings.values()):
        raise ValueError("Completa los cinco apartados de revisión.")
    if any(view not in VIEWS for view in references):
        raise ValueError("Vista de referencia no compatible.")
    if len(notes) > 4000:
        raise ValueError("Limita las indicaciones a 4000 caracteres.")
    directory = Path(run["directory"])
    if not run.get("image"):
        if not references.get("front"):
            raise ValueError("Añade una referencia de frente para comparar este GLB.")
        copy_image(references["front"], directory / "image.png")
        run["image"] = str(directory / "image.png")
        save_run(run)
    review_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
    snapshot_dir = directory / "references" / review_id
    saved = {}
    # Validate every reference before moving the complete snapshot into place.
    with tempfile.TemporaryDirectory(dir=directory, prefix="review-tmp-") as temporary:
        for view, image_path in references.items():
            if image_path:
                copy_image(image_path, Path(temporary) / f"{view}.png")
        if any(Path(temporary).iterdir()):
            snapshot_dir.parent.mkdir(exist_ok=True)
            snapshot_dir.mkdir()
            for source in Path(temporary).iterdir():
                target = snapshot_dir / source.name
                source.replace(target)
                saved[source.stem] = {"path": target.relative_to(directory).as_posix(), "sha256": file_hash(target)}
    plan = correction_plan(ratings, notes)
    review = {
        "id": review_id, "run_id": run["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "manual_visual_review", "model_sha256": file_hash(run["model"]),
        "source_image": {"path": "image.png", "sha256": file_hash(run["image"])},
        "references": saved, "ratings": ratings, "notes": notes.strip(),
        "correction_plan": plan,
    }
    path = directory / f"review_{review_id}.json"
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path), plan, package_run(run)
