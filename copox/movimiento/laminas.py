"""Láminas y GIF de las pruebas de movimiento (frames de Godot o de CHXP).

python -m copox.movimiento.laminas clips  CARPETA salida.png --vista -35 [--clips Wave,Think]
python -m copox.movimiento.laminas poses  CARPETA salida.png --vista -35 --cols 5
python -m copox.movimiento.laminas gif    CARPETA salida.gif [--fps 15 --tam 320]
"""
from __future__ import annotations
import argparse, glob, os, re
from PIL import Image, ImageDraw

SELLO = (24, 26, 32)


def _etiquetar(o: Image.Image, txt: str, xy):
    ImageDraw.Draw(o).text(xy, txt, fill=SELLO)


def _frames(carpeta: str, vista: str):
    """{clip: [rutas ordenadas]} para archivos clip__v<vista>__NN.png"""
    out = {}
    for f in glob.glob(os.path.join(carpeta, f"*__v{vista}__*.png")):
        m = re.match(r"(.+)__v(-?\d+)__(\d+)\.png$", os.path.basename(f))
        if m:
            out.setdefault(m.group(1), []).append((int(m.group(3)), f))
    return {k: [f for _, f in sorted(v)] for k, v in out.items()}


def lamina_clips(carpeta, salida, vista="-35", clips=None, titulo=""):
    fr = _frames(carpeta, vista)
    orden = clips or sorted(fr)
    orden = [c for c in orden if c in fr]
    t = Image.open(fr[orden[0]][0]).width
    n = max(len(fr[c]) for c in orden)
    eti, cab = 150, 24
    o = Image.new("RGB", (eti + n * t, cab + len(orden) * t), "white")
    _etiquetar(o, titulo or f"vista {vista}°  ·  {n} frames por clip, de 0 a 100 %", (6, 6))
    for r, c in enumerate(orden):
        _etiquetar(o, c, (6, cab + r * t + t // 2))
        for k, f in enumerate(fr[c]):
            o.paste(Image.open(f).convert("RGB"), (eti + k * t, cab + r * t))
    o.save(salida)
    return o.size


def lamina_poses(carpeta, salida, vista="-35", cols=5, ultimo=True):
    fr = _frames(carpeta, vista)
    orden = sorted(fr)
    t = Image.open(fr[orden[0]][0]).width
    filas = (len(orden) + cols - 1) // cols
    o = Image.new("RGB", (cols * t, filas * (t + 16)), "white")
    for k, c in enumerate(orden):
        x, y = (k % cols) * t, (k // cols) * (t + 16)
        o.paste(Image.open(fr[c][-1 if ultimo else 0]).convert("RGB"), (x, y))
        _etiquetar(o, c, (x + 4, y + t + 2))
    o.save(salida)
    return o.size


def gif(carpeta, salida, fps=15, tam=320, patron="f_*.png"):
    fs = sorted(glob.glob(os.path.join(carpeta, patron)))
    ims = [Image.open(f).convert("RGB").resize((tam, tam), Image.LANCZOS) for f in fs]
    pal = ims[len(ims) // 2].quantize(colors=128, method=Image.MEDIANCUT)
    q = [i.quantize(palette=pal, dither=Image.NONE) for i in ims]
    q[0].save(salida, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True)
    return len(q)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tipo", choices=["clips", "poses", "gif"])
    ap.add_argument("carpeta"); ap.add_argument("salida")
    ap.add_argument("--vista", default="-35"); ap.add_argument("--clips", default="")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--fps", type=float, default=15); ap.add_argument("--tam", type=int, default=320)
    a = ap.parse_args(argv)
    if a.tipo == "clips":
        print(lamina_clips(a.carpeta, a.salida, a.vista, [c for c in a.clips.split(",") if c] or None))
    elif a.tipo == "poses":
        print(lamina_poses(a.carpeta, a.salida, a.vista, a.cols))
    else:
        print(gif(a.carpeta, a.salida, a.fps, a.tam), "frames")


if __name__ == "__main__":
    main()
