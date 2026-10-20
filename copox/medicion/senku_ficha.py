"""SENKU · propone la ficha de un personaje desde su hoja de referencia (19 oct 2026).

Admin: que el paso «referencia → ficha» deje de hacerse a ojo. Con la hoja (y su .senku.json) y el esqueleto de la base
congelada, SENKU alinea la hoja, toma muestras de color por región (pelo, piel, torso, centro del pecho, mangas,
pantalón, calzado), las lleva al color MÁS CERCANO de la paleta ALTH (ΔE76) y deduce:
  - conjunto de ropa del catálogo (hoy: traje_chaleco si hay torso oscuro + V clara al centro + mangas claras);
  - calzado (oscuro → zapato; claro → tenis); pelo (color; el peinado se elige o se hace con peinar-personaje).
Sale un BORRADOR de ficha (personajes/<nombre>.json) con `_evidencia` (colores medidos, ΔE, confianza) y una imagen
con las zonas muestreadas. Un color con ΔE > 10 NO se inventa: se marca para proponérselo a Admin.

Uso: python -m copox.medicion.senku_ficha HOJA.jpg --nombre ALASTOR_V01 [--salida personajes/alastor.json]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

from . import senku_ref as sr

DE_MAX = 10.0


def _paleta():
    from copox.render import chxp2
    p = chxp2.paleta_spec()
    nombres = list(p)
    lab = chxp2._lab(np.array([chxp2._hex_rgb(p[n]) for n in nombres]))
    return nombres, p, lab


def _dominante(px, k=3):
    """Color dominante de una zona (mediana del grupo más grande por k-medias simple)."""
    px = px.reshape(-1, 3).astype(float)
    if len(px) < 10:
        return None, 0.0
    rng = np.random.default_rng(0)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(12):
        d = ((px[:, None] - c[None]) ** 2).sum(2)
        lab = d.argmin(1)
        c = np.array([px[lab == i].mean(0) if (lab == i).any() else c[i] for i in range(k)])
    cuenta = np.bincount(lab, minlength=k)
    i = cuenta.argmax()
    return np.median(px[lab == i], 0), float(cuenta[i] / len(px))


def _a_paleta(rgb, pal):
    from copox.render import chxp2
    nombres, p, lab = pal
    q = chxp2._lab(np.asarray(rgb, float) / 255.0)
    d = np.linalg.norm(lab - q, axis=1)
    i = int(d.argmin())
    return {"medido": "#%02X%02X%02X" % tuple(int(round(x)) for x in rgb), "paleta": nombres[i], "hex": p[nombres[i]],
            "dE": round(float(d[i]), 1), "nuevo": bool(d[i] > DE_MAX)}


def proponer(hoja_img, nombre, base_glb=None, img_salida=None):
    from copox import entorno
    base_glb = base_glb or entorno.BASE
    hoja = sr.cargar_hoja(hoja_img)
    J = sr.esqueleto(base_glb)
    V0, _ = sr.malla_visible(base_glb)
    al, avisos = sr.alinear(hoja, J, altura_modelo=float(V0[:, 1].max()))
    v = "frente"
    f = hoja[v]; a = f["img"]; obj = f["objeto"]
    e, u0, piso = al[v][:3]

    def fila(y):
        return int(round(piso - y * e))

    def col(x):
        return int(round(u0 + x * e))

    y = {n: float(J[n][1]) for n in ("Hips", "Neck", "Head", "LeftUpperArm", "LeftLowerArm", "LeftFoot", "LeftHand")
         if n in J}
    xb = {n: float(J[n][0]) for n in ("LeftUpperArm", "LeftLowerArm", "LeftHand") if n in J}
    techo = int(np.nonzero(obj.any(1))[0].min())
    hb = fila(y["Neck"]) - techo                                      # alto de la banda de la cabeza (px)
    cab = f["cabeza"] if f["cabeza"].any() else obj
    cc = np.nonzero(cab[techo + int(0.8 * hb)])[0]
    cx = int((cc.min() + cc.max()) / 2) if len(cc) else int(u0)
    hw = int(cc.max() - cc.min()) if len(cc) else int(0.25 * hb)      # ancho de la cara a la altura de las mejillas
    zonas = {   # (fila0, fila1, col0, col1) en píxeles de la hoja (vista de frente, personaje en T)
        # la cabeza chibi no sigue al esqueleto: se mide en la banda techo→cuello de la propia hoja
        "pelo": (techo + int(0.04 * hb), techo + int(0.26 * hb), cx - int(0.10 * hw), cx + int(0.10 * hw)),
        "piel": (techo + int(0.78 * hb), techo + int(0.85 * hb), cx - int(0.30 * hw), cx - int(0.18 * hw)),
        "torso": (fila(y["Neck"] - 0.07), fila(y["Hips"] + 0.03), col(-0.08), col(-0.03)),
        "centro": (fila(y["Neck"] - 0.03), fila(y["Neck"] - 0.07), col(-0.006), col(0.006)),
        "mangas": (fila(y["LeftUpperArm"] + 0.02), fila(y["LeftUpperArm"] - 0.02),
                   col(-(xb["LeftUpperArm"] + 0.02)), col(-(xb["LeftUpperArm"] + 0.06))),
        "pantalon": (fila(y["Hips"] - 0.04), fila(y["LeftFoot"] + 0.04), col(-0.06), col(-0.02)),
        "calzado": (fila(y["LeftFoot"] - 0.005), fila(0.005), col(-0.07), col(-0.02)),
    }
    pal = _paleta()
    medidas = {}
    for k, (r0, r1, c0, c1) in zonas.items():
        r0, r1 = sorted((max(r0, 0), max(r1, 0))); c0, c1 = sorted((max(c0, 0), max(c1, 0)))
        m = obj[r0:r1 + 1, c0:c1 + 1]
        px = a[r0:r1 + 1, c0:c1 + 1][m]
        rgb, frac = _dominante(px)
        medidas[k] = None if rgb is None else dict(_a_paleta(rgb, pal), cobertura=round(frac, 2), caja=[r0, r1, c0, c1])

    def lum(k):
        return None if not medidas.get(k) else float(np.mean([int(medidas[k]["medido"][i:i + 2], 16) for i in (1, 3, 5)]))
    notas = list(avisos)
    ropa, conf = "ninguna", 0.3
    if lum("torso") is not None and lum("mangas") is not None and lum("centro") is not None:
        if lum("torso") < 90 and lum("mangas") > 170:
            ropa, conf = "traje_chaleco", 0.8 if medidas["torso"]["hex"] != medidas["centro"]["hex"] else 0.6
        elif abs(lum("torso") - lum("mangas")) < 25:
            notas.append("torso y mangas del mismo color: ¿saco/abrigo/suéter? No está en el catálogo → research brief "
                         "+ prenda nueva (skill vestir-personaje)")
    calzado = "zapato" if (lum("calzado") or 255) < 90 else "tenis"
    col_ = {}
    if ropa == "traje_chaleco":
        col_ = {"camisa": medidas["mangas"]["hex"], "chaleco": medidas["torso"]["hex"],
                "pantalon": medidas["pantalon"]["hex"], "boton": "#2C2320"}
        # corbata: lo que no es camisa en la columna central
        if medidas["centro"]["hex"] not in (col_["camisa"],):
            col_["corbata"] = medidas["centro"]["hex"]
    nuevos = [k for k, m in medidas.items() if m and m["nuevo"]]
    if nuevos:
        notas.append("colores fuera de paleta (ΔE > %d) en %s: proponer a Admin antes de usar" % (DE_MAX, ", ".join(nuevos)))
    ficha = {
        "nombre": nombre,
        "descripcion": f"BORRADOR propuesto por SENKU desde {os.path.basename(hoja_img)}; revisar con Admin (Lápiz).",
        "base": None, "pelo": "PENDIENTE (color %s; elegir del catálogo o peinar-personaje)" % (medidas["pelo"] or {}).get("hex"),
        "calzado": calzado, "manos": "abierta", "visible": {"CAPA_SHORT": False},
        "ropa": {"conjunto": ropa, "colores": col_, "telas": {"camisa": "tafetan_suave", "chaleco": "lana_cerrada",
                                                               "corbata": "saten", "pantalon": "sarga", "boton": "cuero"} if ropa != "ninguna" else {},
                 "params": {}},
        "chxp": {"tipo": "personaje", "ref": os.path.relpath(hoja_img, entorno.RAIZ), "ref_2x2": hoja["_config"].get("disposicion") == "2x2",
                 "brief": "ropa_capas,zapato,pelvis", "gif": ["Walk-loop", "Run-loop", "Sit-pose"]},
        "publicar": {"carpeta": nombre.split("_")[0].lower(), "nombre": nombre, "nota": "primera versión desde ficha",
                     "estado": "SIN APROBAR"},
        "_evidencia": {"medidas": medidas, "confianza_ropa": conf, "notas": notas},
    }
    if img_salida:
        im = Image.fromarray(a).convert("RGB"); d = ImageDraw.Draw(im)
        for k, m in medidas.items():
            if m:
                r0, r1, c0, c1 = m["caja"]
                d.rectangle([c0, r0, c1, r1], outline=(255, 0, 0), width=2)
                d.text((c1 + 3, r0), f"{k} {m['hex']} ΔE{m['dE']}", fill=(200, 0, 0))
        im.save(img_salida)
    return ficha


def main():
    ap = argparse.ArgumentParser(description="SENKU: hoja de referencia → borrador de ficha de personaje")
    ap.add_argument("hoja")
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--salida")
    ap.add_argument("--imagen")
    a = ap.parse_args()
    f = proponer(a.hoja, a.nombre, img_salida=a.imagen)
    txt = json.dumps(f, indent=2, ensure_ascii=False)
    if a.salida:
        open(a.salida, "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
