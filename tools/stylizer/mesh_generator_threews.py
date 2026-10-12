"""Experimental three.ws draft adapter. No payment or paid-tier upgrade."""

import hashlib
import sys
import time
from pathlib import Path

import requests

API_ROOT = "https://three.ws"


def response_json(response):
    if response.status_code == 402:
        raise RuntimeError("three.ws solicita pago para esta operación. No se ha realizado ningún pago.")
    if response.status_code == 429:
        raise RuntimeError("three.ws agotó la cuota o está saturado. Reintenta más tarde.")
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("three.ws devolvió una respuesta inesperada.")
    return data


def upload_image_to_threews(image_path):
    image_data = Path(image_path).read_bytes()
    data = response_json(requests.post(
        f"{API_ROOT}/api/forge-upload",
        json={"content_type": "image/png", "size_bytes": len(image_data),
              "checksum_sha256": hashlib.sha256(image_data).hexdigest()},
        timeout=30,
    ))
    upload_url = data.get("upload_url") or data.get("url")
    public_url = data.get("public_url") or data.get("file_url")
    if not upload_url or not public_url:
        raise RuntimeError("three.ws no devolvió las URLs de subida y lectura de la imagen.")
    response = requests.put(upload_url, data=image_data, headers={"Content-Type": "image/png"}, timeout=60)
    response.raise_for_status()
    return public_url


def request_job(public_url, backend=None):
    payload = {"image_urls": [public_url], "tier": "draft", "path": "image"}
    if backend:
        payload["backend"] = backend
    data = response_json(requests.post(f"{API_ROOT}/api/forge", json=payload, timeout=120))
    return data.get("job_id") or data.get("job") or data.get("id"), data


def wait_for_job(job_id, timeout_seconds=300):
    deadline = time.monotonic() + timeout_seconds
    delay = 5
    while time.monotonic() < deadline:
        time.sleep(min(delay, max(0, deadline - time.monotonic())))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            response = requests.get(
                f"{API_ROOT}/api/forge", params={"job": job_id}, timeout=min(30, remaining)
            )
            data = response_json(response)
        except (requests.Timeout, requests.ConnectionError):
            continue
        state = data.get("status") or data.get("state")
        if state in {"completed", "done", "succeeded"}:
            return data
        if state in {"failed", "error", "cancelled", "canceled"}:
            raise RuntimeError(f"three.ws: {data.get('error', 'falló la generación')}")
        try:
            delay = min(60, max(1, float(data.get("retryAfter", 5))))
        except (TypeError, ValueError):
            delay = 5
    raise TimeoutError("three.ws no terminó en 5 minutos. El trabajo remoto podría seguir activo.")


def download_glb(data, output_file):
    candidates = [data, data.get("result"), data.get("output")]
    url = next((item.get("glb_url") or item.get("glbUrl") for item in candidates
                if isinstance(item, dict) and (item.get("glb_url") or item.get("glbUrl"))), None)
    if not url:
        raise RuntimeError("three.ws terminó sin devolver un enlace GLB.")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    Path(output_file).write_bytes(response.content)
    return True


def generate_3d_mesh_threews(image_path, output_file="model.glb", prefer_backend=None):
    public_url = upload_image_to_threews(image_path)
    job_id, data = request_job(public_url, prefer_backend)
    state = data.get("status") or data.get("state")
    if state in {"failed", "error", "cancelled", "canceled"}:
        raise RuntimeError(f"three.ws: {data.get('error', 'falló la generación')}")
    if state not in {"completed", "done", "succeeded"}:
        if not job_id:
            raise RuntimeError("three.ws no devolvió un identificador de trabajo.")
        data = wait_for_job(job_id)
    return download_glb(data, output_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python mesh_generator_threews.py <imagen.png> [backend]")
    try:
        generate_3d_mesh_threews(sys.argv[1], prefer_backend=sys.argv[2] if len(sys.argv) > 2 else None)
    except Exception as error:
        sys.exit(str(error))
