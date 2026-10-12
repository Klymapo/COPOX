import sys
import os
import requests
import config  # Load .env when running this script directly.

API_URL = "https://apihub.agnes-ai.com/v1/images/generations"

def generate_image_agnes(prompt, output_file="output_agnes.png"):
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        raise RuntimeError("Configura AGNES_API_KEY para generar imágenes desde texto, o usa una imagen existente.")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "agnes-image-2.5-flash",
        "prompt": prompt,
        "size": "1K",
        "ratio": "1:1",
        "return_base64": False
    }

    print("Enviando peticion a Agnes AI...")
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()

        image_url = data.get("data", [{}])[0].get("url")
        if not image_url:
            print(f"Respuesta inesperada: {data}")
            return False

        print("Imagen generada; descargando resultado…")

        img_response = requests.get(image_url, timeout=120)
        img_response.raise_for_status()
        with open(output_file, "wb") as f:
            f.write(img_response.content)
        print(f"Imagen guardada: {output_file}")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
        if response.text:
            print(f"Respuesta del servidor: {response.text[:500]}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python image_generator_agnes.py \"<prompt>\"")
        sys.exit(1)
    success = generate_image_agnes(sys.argv[1])
    sys.exit(0 if success else 1)
