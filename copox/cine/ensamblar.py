"""Cuadros PNG → MP4 (H.264, yuv420p) con ffmpeg. Uso: python -m copox.cine.ensamblar DIR_CUADROS SALIDA.mp4 --fps 24"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess


def ensamblar(cuadros, salida, fps=24):
    fs = sorted(glob.glob(os.path.join(cuadros, "*.png")))
    if not fs:
        raise FileNotFoundError(f"sin cuadros en {cuadros}")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("falta ffmpeg")
    lista = os.path.join(cuadros, "_lista.txt")
    with open(lista, "w") as f:
        for p in fs:
            f.write(f"file '{os.path.abspath(p)}'\nduration {1 / fps:.6f}\n")
        f.write(f"file '{os.path.abspath(fs[-1])}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-vf",
                    "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", salida], check=True)
    return {"mp4": salida, "cuadros": len(fs), "fps": fps}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cuadros"); ap.add_argument("salida"); ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    print(ensamblar(a.cuadros, a.salida, a.fps))
