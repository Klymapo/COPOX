"""CLI entry point. python pipeline.py --help"""

import argparse
import sys

from pipeline_core import OUTPUT_ROOT, run_pipeline
from mesh_service import PROVIDERS


def main():
    parser = argparse.ArgumentParser(description="Convierte una idea o una imagen en un modelo 3D.")
    parser.add_argument("idea", nargs="?", help="Idea en lenguaje natural")
    parser.add_argument("--image", help="Imagen PNG, JPEG o WebP; una sola vista del personaje")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT), help="Carpeta de generaciones")
    parser.add_argument("--provider", choices=PROVIDERS, default="auto", help="auto: TRELLIS.2 y luego three.ws draft")
    args = parser.parse_args()
    if bool(args.idea and args.idea.strip()) == bool(args.image):
        parser.error("Indica una idea o --image, exclusivamente.")
    run = run_pipeline(idea=args.idea, image_path=args.image, provider=args.provider, output_root=args.output_dir, progress=print)
    print(f"Archivos: {run['directory']}")
    print(f"ZIP: {run['directory']}/{run['id']}.zip")
    if run["error"]:
        print(run["error"], file=sys.stderr)
        return 1
    print(f"Modelo: {run['model']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
