"""Export an UNREVIEWED Stylizer candidate for ALTH-META/COPOX.

The bridge is deliberately read-only with respect to input GLBs and approved assets.
It does not rescale, decimate, import rigs into Blender, or promote any candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from mesh_service import validate_glb

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "spec" / "alth_spec.json"
APPROVED_ASSETS = REPO_ROOT / "assets"


def _metadata(path: Path) -> dict:
    with path.open("rb") as stream:
        header = stream.read(20)
        if len(header) != 20:
            raise ValueError("GLB header incompleto")
        _, _, _, size, _ = struct.unpack("<4sIIII", header)
        payload = stream.read(size)
    return json.loads(payload)


def describe_glb(source: str | Path) -> dict:
    path = Path(source).expanduser().resolve(strict=True)
    validate_glb(path)
    gltf = _metadata(path)
    meshes = gltf.get("meshes") or []
    morphs = any((p.get("targets") or []) for mesh in meshes for p in mesh.get("primitives", []))
    rigged = bool(gltf.get("skins") or gltf.get("animations") or morphs)
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
        "mesh_type": "rigged_or_animated" if rigged else "static_or_unidentified",
        "has_skins": bool(gltf.get("skins")),
        "has_animations": bool(gltf.get("animations")),
        "has_morph_targets": bool(morphs),
    }


def create_candidate(source: str | Path, output_dir: str | Path, asset_id: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", asset_id):
        raise ValueError("asset_id debe ser un identificador corto sin rutas")
    source_path = Path(source).expanduser().resolve(strict=True)
    destination = Path(output_dir).expanduser().resolve()
    if destination == APPROVED_ASSETS or APPROVED_ASSETS in destination.parents:
        raise ValueError("No escribir candidatos en el árbol de assets aprobados")
    if destination == source_path.parent:
        raise ValueError("La salida debe estar separada del archivo de origen")
    info = describe_glb(source_path)
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("version") != "2.0":
        raise RuntimeError("Especificación ALTH inesperada; revisar contrato de escala")
    record = {
        "schema_version": 1,
        "source_tool": "stylizer",
        "asset_id": asset_id,
        "source_glb": str(source_path),
        "source": info,
        "alth_spec_version": spec["version"],
        "scale_reference": "Theo Alpha",
        "approval_state": "UNREVIEWED",
        "input_modified": False,
        "geometry_converted": False,
        "audits": {
            "glb_header": "PASS",
            "scale": "PENDING",
            "orientation": "PENDING",
            "silhouette": "PENDING",
            "material_quality": "PENDING",
            "reference_likeness": "PENDING",
            "rig_integrity": "PENDING" if info["mesh_type"] == "rigged_or_animated" else "NOT_APPLICABLE"
        },
        "warnings": [
            "Candidato no aprobado; requiere auditoría y revisión visual COPOX/CHSP-X.",
            "No se aplicó la escala ALTH; no usar los 1.8 m predeterminados del preparador para assets ALTH.",
        ],
    }
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / (asset_id + ".alth-candidate.json")
    if target.exists():
        raise FileExistsError("Ya existe el manifiesto: " + str(target))
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Registra un GLB como candidato NO APROBADO de ALTH-META")
    parser.add_argument("--input", required=True, help="Ruta del modelo GLB (no se modifica)")
    parser.add_argument("--output-dir", required=True, help="Carpeta separada para manifiestos")
    parser.add_argument("--asset-id", required=True)
    args = parser.parse_args()
    print(create_candidate(args.input, args.output_dir, args.asset_id))


if __name__ == "__main__":
    main()
