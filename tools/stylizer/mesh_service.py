"""Select a 3D provider; only accept a complete GLB container."""

import json
import struct
from pathlib import Path

from config import redact

PROVIDERS = ("auto", "trellis", "threews")


def validate_glb(path):
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(20)
        if len(header) != 20:
            raise ValueError("Archivo GLB incompleto.")
        magic, version, size, json_size, chunk_type = struct.unpack("<4sIIII", header)
        if magic != b"glTF" or version != 2 or size != path.stat().st_size:
            raise ValueError("La descarga no es un contenedor GLB 2 válido.")
        if chunk_type != 0x4E4F534A or json_size > size - 20 or json_size > 16_000_000:
            raise ValueError("El GLB no contiene una cabecera JSON válida.")
        metadata = json.loads(stream.read(json_size))
        if metadata.get("asset", {}).get("version") != "2.0":
            raise ValueError("Versión de glTF no compatible.")


def reconstruct(image_path, output_file, provider="auto", progress=None):
    if provider not in PROVIDERS:
        raise ValueError("Proveedor desconocido.")
    notify = progress or (lambda message: None)
    providers = ("trellis", "threews") if provider == "auto" else (provider,)
    output = Path(output_file)
    temporary = output.with_name("model.partial.glb")
    attempts = []
    for name in providers:
        temporary.unlink(missing_ok=True)
        notify(f"Generando 3D con {name}…")
        try:
            if name == "trellis":
                from mesh_generator import generate_3d_mesh
                ok = generate_3d_mesh(str(image_path), output_file=str(temporary))
            else:
                from mesh_generator_threews import generate_3d_mesh_threews
                ok = generate_3d_mesh_threews(str(image_path), output_file=str(temporary))
            if not ok:
                raise RuntimeError("El proveedor no pudo completar la generación.")
            validate_glb(temporary)
            temporary.replace(output)
            attempts.append({"provider": name, "status": "completed"})
            return {"model": str(output), "provider": name, "attempts": attempts, "error": None}
        except Exception as error:
            attempts.append({"provider": name, "status": "failed", "error": redact(error)})
        finally:
            temporary.unlink(missing_ok=True)
    details = "; ".join(f"{item['provider']}: {item['error']}" for item in attempts)
    return {"model": None, "provider": None, "attempts": attempts,
            "error": f"No se pudo generar el modelo. Tu imagen quedó guardada. {details}"}
