import sys
import os
import shutil
from gradio_client import Client, handle_file
import config  # Load .env when running this script directly.


def predict_bounded(client, **kwargs):
    job = client.submit(**kwargs)
    try:
        return job.result(timeout=600)
    except TimeoutError as error:
        job.cancel()
        raise TimeoutError("TRELLIS.2 excedió 10 minutos en esta etapa; se solicitó cancelación.") from error

def generate_3d_mesh(image_path, output_file="model.glb"):
    if not os.path.exists(image_path):
        print(f"Error: no existe la imagen {image_path}", file=sys.stderr)
        return False

    print("Conectando al Space de TRELLIS.2...")
    client = Client("microsoft/TRELLIS.2", token=os.environ.get("HF_TOKEN") or None,
                    httpx_kwargs={"timeout": 60}, verbose=False)

    print("[1/4] Iniciando sesion...")
    try:
        predict_bounded(client, api_name="/start_session")
    except Exception as e:
        print(f"Advertencia en start_session: {e}", file=sys.stderr)

    print("[2/4] Preprocesando imagen...")
    try:
        prepared_image = predict_bounded(client,
            input=handle_file(image_path),
            api_name="/preprocess_image"
        )
    except Exception as e:
        raise RuntimeError(f"Falló el preprocesamiento de TRELLIS.2: {e}") from e

    if isinstance(prepared_image, (list, tuple)):
        prepared_image = prepared_image[0]
    if isinstance(prepared_image, dict):
        prepared_image = prepared_image.get("path") or prepared_image.get("url")
    if not prepared_image:
        raise RuntimeError("TRELLIS.2 no devolvió la imagen preprocesada.")

    print("[3/4] Generando geometria 3D (esto tarda 2-5 minutos)...")
    try:
        predict_bounded(client,
            image=handle_file(prepared_image),
            seed=0,
            resolution="1024",
            ss_guidance_strength=7.5,
            ss_guidance_rescale=0.7,
            ss_sampling_steps=12,
            ss_rescale_t=5.0,
            shape_slat_guidance_strength=7.5,
            shape_slat_guidance_rescale=0.5,
            shape_slat_sampling_steps=12,
            shape_slat_rescale_t=3.0,
            tex_slat_guidance_strength=1.0,
            tex_slat_guidance_rescale=0.0,
            tex_slat_sampling_steps=12,
            tex_slat_rescale_t=3.0,
            api_name="/image_to_3d"
        )
    except Exception as e:
        raise RuntimeError(f"TRELLIS.2 no pudo reconstruir: {e}") from e

    print("[4/4] Extrayendo archivo GLB...")
    try:
        result = predict_bounded(client,
            decimation_target=300000,
            texture_size=2048,
            api_name="/extract_glb"
        )
    except Exception as e:
        print(f"Error en extract_glb: {e}", file=sys.stderr)
        return False

    print(f"Respuesta de extract_glb: {result}")

    glb_path = None
    if isinstance(result, (list, tuple)):
        for item in result:
            if isinstance(item, str) and os.path.exists(item):
                if item.endswith(".glb") or "glb" in item.lower():
                    glb_path = item
                    break
            if isinstance(item, dict) and item.get("path"):
                if item["path"].endswith(".glb"):
                    glb_path = item["path"]
                    break
    elif isinstance(result, str) and os.path.exists(result):
        glb_path = result

    if glb_path:
        shutil.copy(glb_path, output_file)
        print(f"Modelo 3D guardado: {output_file}")
        return True

    print("No se encontro un archivo GLB en la respuesta.", file=sys.stderr)
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python mesh_generator.py <ruta_imagen>")
        sys.exit(1)
    success = generate_3d_mesh(sys.argv[1])
    sys.exit(0 if success else 1)
