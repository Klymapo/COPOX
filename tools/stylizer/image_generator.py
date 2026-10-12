import sys
import json
import time
import urllib.parse
import requests

def generate_image(prompt, output_file="output.png", max_retries=3):
    # Codificación robusta para prompts largos
    encoded = urllib.parse.quote(prompt, safe='')
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux"
    
    for attempt in range(1, max_retries + 1):
        print(f"Intento {attempt}/{max_retries}...")
        try:
            response = requests.get(url, timeout=180)
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"Imagen guardada: {output_file}")
                return True
            else:
                print(f"Error {response.status_code}. Reintentando en 5 segundos...")
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}. Reintentando en 5 segundos...")
            time.sleep(5)
    
    print("No se pudo generar la imagen después de varios intentos.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python image_generator.py \"<prompt>\"")
        sys.exit(1)
    success = generate_image(sys.argv[1])
    sys.exit(0 if success else 1)
