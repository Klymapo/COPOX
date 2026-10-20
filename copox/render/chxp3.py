"""CHXP V3 · ver y medir en una llamada (19 oct 2026).

= CHXP V2 (render Godot: hoja, pasadas, GIF con resortes, reporte) + auditoría (copox/render/auditoria.py): SENKU contra
la hoja de referencia, cobertura del pelo, resortes, paleta, apoyo en el piso, protección de Theo y las reglas de las
skills (vetan las medibles implementadas; las demás salen como pendientes o checklist).
Escribe <nombre>_AUDITORIA.json, agrega el veredicto al REPORTE y una franja con las revisiones al pie de la HOJA.

Uso:
  python -m copox.render.chxp3 GLB --tipo personaje|pelo|ropa|calzado|objeto|edificio --salida DIR
         [--ref imagen.jpg [--ref-2x2]] [--hoja hoja_senku.jpg] [--vistas personaje|cabeza|objeto|edificio] [--gif Idle-loop,Run-loop]
         [--visible nodo=0,...] [--ocultar NODO,...] [--rapido]
Código de salida: 0 PASS, 1 FAIL, 2 N-A (nada aplicable).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import auditoria, chxp2

COLOR = {"PASS": (60, 150, 80), "FAIL": (200, 60, 50), "N-A": (130, 130, 140), "PENDIENTE": (190, 140, 40)}


def _franja(ruta_hoja, aud):
    from PIL import Image, ImageDraw
    if not os.path.exists(ruta_hoja):
        return
    im = Image.open(ruta_hoja).convert("RGB")
    filas = aud["revisiones"]
    alto = 46 + 22 * (len(filas) + 2)
    out = Image.new("RGB", (im.width, im.height + alto), (250, 250, 250))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    fuente = chxp2._fuente(15) if hasattr(chxp2, "_fuente") else None
    y = im.height + 10
    d.text((16, y), f"CHXP V3 · auditoría · {aud['tipo']} · VEREDICTO {aud['veredicto']}  "
                    f"({aud['pass']} PASS / {aud['fail']} FAIL / {aud['na']} N-A)", fill=COLOR.get(aud["veredicto"], (0, 0, 0)), font=fuente)
    y += 28
    for f in filas:
        med = f["medida"]
        if isinstance(med, dict):
            med = " ".join(f"{k}:{v}" for k, v in med.items())
        d.text((16, y), f"{f['veredicto']:4}  {f['id']}: {med}  (umbral {f['umbral']})"[:160], fill=COLOR[f["veredicto"]], font=fuente)
        y += 22
    d.text((16, y), f"skills: {len(aud['pendientes_skills'])} reglas medibles pendientes · "
                    f"{len(aud['checklist_skills'])} de revisión visual (ver AUDITORIA.json)", fill=(90, 90, 90), font=fuente)
    out.save(ruta_hoja)


def render(glb, salida, tipo, ref=None, ocultar=(), hoja=None, base=None, brief=None, **kw):
    rep = chxp2.render(glb, salida, ref=ref, version="V3", **kw)
    nombre = kw.get("nombre") or os.path.splitext(os.path.basename(glb))[0].lower()
    aud = auditoria.auditar(glb, tipo, rep, ref=hoja or ref, ocultar=ocultar, salida=salida, base=base, brief=brief)
    with open(os.path.join(salida, f"{nombre}_AUDITORIA.json"), "w") as f:
        json.dump(aud, f, indent=2, ensure_ascii=False, default=str)
    rep["auditoria"] = {"veredicto": aud["veredicto"], "pass": aud["pass"], "fail": aud["fail"], "na": aud["na"]}
    with open(os.path.join(salida, f"{nombre}_REPORTE.json"), "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False, default=str)
    _franja(os.path.join(salida, f"{nombre}_HOJA.png"), aud)
    return rep, aud


def main():
    ap = argparse.ArgumentParser(description="CHXP V3: render + auditoría (SENKU + skills)")
    ap.add_argument("glb")
    ap.add_argument("--tipo", required=True, choices=auditoria.TIPOS)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ref")
    ap.add_argument("--ref-2x2", action="store_true")
    ap.add_argument("--base", help="GLB del que deriva (para revisar que no se pierdan clips, huesos ni morphs)")
    ap.add_argument("--brief", help="temas de docs/investigacion separados por coma (técnica nueva)")
    ap.add_argument("--hoja", help="hoja para SENKU (con .senku.json); por defecto --ref")
    ap.add_argument("--vistas", default="personaje", choices=list(chxp2.VISTAS))
    ap.add_argument("--visible", default="")
    ap.add_argument("--ocultar", default="", help="nodos a ignorar en SENKU (p. ej. guías)")
    ap.add_argument("--gif", default="")
    ap.add_argument("--tam", type=int, default=1024)
    ap.add_argument("--sin-resortes", action="store_true")
    ap.add_argument("--rapido", action="store_true", help="iteración: 512 px, sin GIFs (las compuertas son las mismas)")
    a = ap.parse_args()
    from copox import entorno
    entorno.preparar()
    if a.rapido:
        a.tam, a.gif = 512, ""
    vis = {kv.split("=")[0]: kv.split("=")[1] not in ("0", "no", "false") for kv in a.visible.split(",") if "=" in kv}
    rep, aud = render(a.glb, a.salida, a.tipo, ref=a.ref, hoja=a.hoja, base=a.base, brief=a.brief, ocultar=tuple(x for x in a.ocultar.split(",") if x),
                      vistas=a.vistas, visible=vis, gifs=[g for g in a.gif.split(",") if g], tam=a.tam,
                      ref_2x2=a.ref_2x2, resortes=not a.sin_resortes)
    print(json.dumps({"asset": rep["asset"], "veredicto": aud["veredicto"], "pass": aud["pass"], "fail": aud["fail"],
                      "na": aud["na"], "fallas": [f["id"] for f in aud["revisiones"] if f["veredicto"] == "FAIL"]},
                     ensure_ascii=False))
    sys.exit({"PASS": 0, "FAIL": 1}.get(aud["veredicto"], 2))


if __name__ == "__main__":
    main()
