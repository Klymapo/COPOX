"""Tira de CHXP con morphs: python -m copox.movimiento.tira_morphs MODELO.glb salida.png "vista" "m1:1,m2:0.5" "..." """
import sys
from PIL import Image, ImageDraw
from copox.render import Sesion


def tira(glb, salida, vista, combos, tam=300, recorte=None):
    s = Sesion(glb)
    ims = []
    for c in combos:
        r = s.render(f"{vista};tam={tam}" + (f";morph={c}" if c else ""), autor="elio")
        im = Image.fromarray(r.imagen if hasattr(r, "imagen") else r.rgb).convert("RGB") if False else None
        r.guardar(salida + ".tmp.png", sello=False)
        im = Image.open(salida + ".tmp.png").convert("RGB")
        if recorte:
            im = im.crop(recorte)
        ims.append((c or "reposo", im))
    w, h = ims[0][1].size
    o = Image.new("RGB", (w * len(ims), h + 16), "white")
    d = ImageDraw.Draw(o)
    for k, (c, im) in enumerate(ims):
        o.paste(im, (k * w, 0)); d.text((k * w + 3, h + 2), c[:40], fill=(20, 20, 20))
    o.save(salida)
    import os; os.remove(salida + ".tmp.png")
    return o.size


if __name__ == "__main__":
    print(tira(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]))
