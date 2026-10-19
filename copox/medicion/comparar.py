"""Compara un GLB con una hoja de referencias imitando pose y cámara.

Uso:
    python -m copox.medicion.comparar manifiesto.json --salida carpeta

Manifiesto (JSON):
{
  "modelo": "ruta.glb",
  "excluir_nodos": [],                       # p. ej. capas que la referencia no tiene
  "poses": [["Idle-loop", 0.0], [null, 0]],  # candidatas; null = pose de reposo
  "elevaciones": [0, 4, 8, 12],
  "distancias": [null, 4.0, 2.5],            # null = ortográfica; números en unidades del modelo
  "referencias": [
    {"id": "frente", "imagen": "hoja.png", "recorte": [x0, y0, x1, y1], "yaw": 0, "ancla": "ojos"},
    {"id": "perfil", "imagen": "hoja.png", "recorte": [...], "yaw": [90, -90], "ancla": "suelo"}
  ]
}
La primera referencia con ancla "ojos" define la unidad ED y la pose/cámara;
las demás comparten escala y línea de suelo (misma hoja, misma cámara).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import paleta, piezas
from .camara import Camara
from .gltf import Modelo
from .raster import Escena, render

ALTURAS = np.round(np.arange(-2.5, 5.01, 0.25), 2)
GRUPOS = {"silueta": [1, 2, 3, 4, 5], "sin_pelo": [2, 3, 4, 5], "piel": [2], "pelo": [1], "oscuro": [4], "azul": [5]}


def clases_rapidas(esc: Escena, cam: Camara, escala, centro, tam, factor=2):
    """Mapa de clases para búsquedas: render real a 1/factor de resolución, re-escalado al tamaño pedido."""
    H, W = tam
    h, w = max(8, H // factor), max(8, W // factor)
    C, _ = render(esc, cam, escala / factor, (centro[0] / factor, centro[1] / factor), (h, w))
    return np.asarray(Image.fromarray(C).resize((W, H), Image.NEAREST))


def _clases_salpicado(esc: Escena, cam: Camara, escala, centro, tam):
    """(Obsoleto) salpicado de puntos; deja huecos en triángulos grandes."""
    H, W = tam
    T = esc.T
    pts = np.concatenate([T.reshape(-1, 3), T.mean(1), (T[:, 0] + T[:, 1]) / 2, (T[:, 1] + T[:, 2]) / 2, (T[:, 0] + T[:, 2]) / 2])
    cls = np.concatenate([np.repeat(esc.clase, 3), esc.clase, esc.clase, esc.clase, esc.clase])
    x, y, z = cam.proyectar(pts)
    X = np.round(centro[0] + x * escala).astype(int)
    Y = np.round(centro[1] - y * escala).astype(int)
    ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
    X, Y, z, cls = X[ok], Y[ok], z[ok], cls[ok]
    o = np.argsort(z)  # lejos -> cerca; la última escritura gana
    C = np.zeros((H, W), np.uint8)
    C[Y[o], X[o]] = cls[o]
    # rellenar huecos de 1 px con la moda de vecinos no-fondo
    for _ in range(2):
        hueco = C == 0
        mejor = np.zeros_like(C)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            v = np.roll(np.roll(C, dy, 0), dx, 1)
            mejor = np.where((mejor == 0) & (v > 0), v, mejor)
        vecinos = sum(((np.roll(np.roll(C, dy, 0), dx, 1) > 0).astype(int)) for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)))
        C = np.where(hueco & (vecinos >= 3), mejor, C)
    return C


def _ref(r, base: Path):
    im = Image.open(base / r["imagen"]).convert("RGB")
    if r.get("recorte"):
        im = im.crop(tuple(r["recorte"]))
    rgb = np.asarray(im)
    C = paleta.segmentar_referencia(rgb)
    # margen de fondo alrededor del panel: el modelo puede sobresalir y no debe recortarse al medirlo
    m = int(r.get("margen", 0.2) * max(C.shape))
    rgb = np.pad(rgb, ((m, m), (m, m), (0, 0)), constant_values=236)
    C = np.pad(C, m, constant_values=paleta.FONDO)
    return rgb, C


def _ojos_px(C):
    o = piezas.ojos(C)
    if len(o) != 2:
        return None
    return (o[0]["cx"] + o[1]["cx"]) / 2, (o[0]["cy"] + o[1]["cy"]) / 2, o[1]["cx"] - o[0]["cx"]


def _iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


def ajustar_frente(modelo, ref_C, poses, elevs, dists, yaw, excluir):
    """Busca pose + elevación + distancia que mejor reproducen la silueta (sin pelo) alineando por ojos."""
    ro = _ojos_px(ref_C)
    if ro is None:
        raise RuntimeError("No se detectaron los dos ojos en la referencia frontal")
    rx, ry, red = ro
    H, W = ref_C.shape
    ref_sin_pelo = np.isin(ref_C, GRUPOS["sin_pelo"])
    escenas = {}
    resultados = []
    for clip, frac in poses:
        key = (clip, frac)
        escenas[key] = esc = Escena(modelo, clip, frac, excluir)
        P = esc.T.reshape(-1, 3)
        objetivo = (0.0, float(np.percentile(P[:, 1], 80)), 0.0)
        for e in elevs:
            for d in dists:
                cam = Camara(yaw=yaw, elevacion=e, distancia=d, objetivo=objetivo)
                # 1) render de exploración para hallar los ojos del modelo
                s0 = 0.8 * H / (P[:, 1].max() - P[:, 1].min())
                C0 = clases_rapidas(esc, cam, s0, (W / 2, H / 2), (H, W))
                mo = _ojos_px(C0)
                if mo is None:
                    continue
                mx, my, med = mo
                s = s0 * red / med
                centro = (rx - (mx - W / 2) * s / s0, ry - (my - H / 2) * s / s0)
                C1 = clases_rapidas(esc, cam, s, centro, (H, W))
                iou = _iou(ref_sin_pelo, np.isin(C1, GRUPOS["sin_pelo"]))
                resultados.append(dict(clip=clip, frac=frac, elevacion=e, distancia=d, iou=iou, escala=s, centro=centro, objetivo=objetivo))
    if not resultados:
        raise RuntimeError("El modelo no mostró dos ojos en ninguna combinación")
    mejor = max(resultados, key=lambda r: r["iou"])
    return mejor, resultados, escenas[(mejor["clip"], mejor["frac"])]


def frente_cara(C, y_ojos, ed):
    """Columna de la punta de la cara (piel) en la franja ojos..ojos+0.6 ED, del lado hacia donde mira:
    el lado donde la piel sobresale más allá del pelo."""
    y0, y1 = int(y_ojos - 0.1 * ed), int(y_ojos + 0.6 * ed)
    band = C[max(y0, 0):y1]
    ps = np.nonzero((band == 2).any(0))[0]
    hs = np.nonzero((band == 1).any(0))[0]
    if not len(ps):
        return None
    if len(hs) and np.mean(ps) < np.mean(hs):
        return float(ps.min())
    return float(ps.max())


def lamina(ruta, ref_rgb, mod_rgb, ref_C, mod_C, titulo):
    a = ref_C != 0
    b = mod_C != 0
    ov = np.full(ref_C.shape + (3,), 245, np.uint8)
    ov[a & ~b] = (215, 60, 60)
    ov[b & ~a] = (60, 95, 215)
    ov[a & b] = (160, 160, 160)
    w = ref_rgb.shape[1]
    out = Image.new("RGB", (w * 4, ref_rgb.shape[0] + 26), (255, 255, 255))
    for i, im in enumerate((ref_rgb, mod_rgb, paleta.colorear(mod_C), ov)):
        out.paste(Image.fromarray(im), (w * i, 26))
    ImageDraw.Draw(out).text((6, 6), titulo + "   [ref | modelo | clases del modelo | rojo: solo ref, azul: solo modelo]", fill=(20, 20, 20))
    out.save(ruta)


def ejecutar(man: dict, base: Path, salida: Path) -> dict:
    salida.mkdir(parents=True, exist_ok=True)
    modelo = Modelo(str(base / man["modelo"]))
    excluir = tuple(man.get("excluir_nodos", []))
    poses = [tuple(p) for p in man.get("poses", [[None, 0.0]])]
    elevs = man.get("elevaciones", [0])
    dists = man.get("distancias", [None])
    refs = man["referencias"]
    frente = next(r for r in refs if r.get("ancla") == "ojos")
    rgbF, CF = _ref(frente, base)
    ajuste, todos, esc = ajustar_frente(modelo, CF, poses, elevs, dists, frente.get("yaw", 0), excluir)
    rx, ry, red = _ojos_px(CF)
    suelo_frente = piezas.extremos(CF)[1]
    reporte = {"modelo": man["modelo"], "sha256_modelo": hashlib.sha256((base / man["modelo"]).read_bytes()).hexdigest(),
               "ajuste": {k: v for k, v in ajuste.items() if k not in ("centro",)}, "busqueda": todos, "vistas": {}}
    s = ajuste["escala"]
    for r in refs:
        rgb, Cr = (rgbF, CF) if r is frente else _ref(r, base)
        H, W = Cr.shape
        yaws = r.get("yaw", 0)
        yaws = yaws if isinstance(yaws, list) else [yaws]
        top_r, bot_r = piezas.extremos(Cr)
        if r is frente:
            ancla_y, ancla_x = ry, rx
        else:
            ancla_y = ry + (bot_r - suelo_frente)  # misma línea de ojos sobre el suelo
            ancla_x = piezas.centro_cabeza(Cr, top_r, bot_r - top_r)
        mejor = None
        for yv in yaws:
            cam = Camara(yaw=yv, elevacion=ajuste["elevacion"], distancia=ajuste["distancia"], objetivo=ajuste["objetivo"])
            if r is frente:
                centro = ajuste["centro"]
            else:
                # el objetivo (centro de cabeza, a la altura usada en el frente) se coloca sobre la cabeza de la ref
                Cp = clases_rapidas(esc, cam, s, (W / 2, H / 2), (H, W))
                tp, bp = piezas.extremos(Cp)
                cx_m = piezas.centro_cabeza(Cp, tp, bp - tp)
                dy_ojo = ajuste["centro"][1] - ry  # desplazamiento objetivo↔ojos del frente
                centro = (W / 2 + (ancla_x - cx_m), ancla_y + dy_ojo)
            Cm, rgbm = render(esc, cam, s, centro, (H, W))
            # silueta + piel + pelo: la piel de la cara decide hacia dónde mira (la silueta sola es casi simétrica)
            iou = (_iou(np.isin(Cr, GRUPOS["sin_pelo"]), np.isin(Cm, GRUPOS["sin_pelo"])) + _iou(Cr == 2, Cm == 2) + _iou(Cr == 1, Cm == 1)) / 3
            if mejor is None or iou > mejor[0]:
                mejor = (iou, yv, Cm, rgbm, cam, centro)
        _, yv, Cm, rgbm, cam, centro = mejor
        xc_r = ancla_x
        xc_m = rx if r is frente else ancla_x
        if r.get("ancla_x") == "cara" and r is not frente:
            # ancla horizontal = punta de la cara (piel) a la altura de los ojos; no depende del volumen de pelo
            fr = frente_cara(Cr, ancla_y, red)
            fm = frente_cara(Cm, ancla_y, red)
            if fr is not None and fm is not None:
                centro = (centro[0] + (fr - fm), centro[1])
                Cm, rgbm = render(esc, cam, s, centro, (H, W))
                xc_r = xc_m = fr
        y_ojo_m = ancla_y
        filas = []
        pr = piezas.perfil_anchos(Cr, ancla_y, red, xc_r, ALTURAS)
        pm = piezas.perfil_anchos(Cm, y_ojo_m, red, xc_m, ALTURAS)
        for h, a, b in zip(ALTURAS, pr, pm):
            if a[2] is None or b[2] is None:
                continue
            filas.append({"altura_ED": float(h), "ref_ancho": round(a[2], 3), "modelo_ancho": round(b[2], 3), "dif": round(b[2] - a[2], 3),
                          "ref_izq": round(a[0], 3), "ref_der": round(a[1], 3), "mod_izq": round(b[0], 3), "mod_der": round(b[1], 3)})
        vista = {"yaw": yv, "camara": cam.dict(), "iou": piezas.iou_por_clase(Cr, Cm, GRUPOS),
                 "medidas_ref": piezas.medidas(Cr, red, ancla_y, xc_r), "medidas_modelo": piezas.medidas(Cm, red, y_ojo_m, xc_m),
                 "perfil_anchos": filas}
        vista["ancla_px"] = {"x": float(xc_r), "y_ojos": float(ancla_y), "ed": float(red), "centro_modelo": [float(centro[0]), float(centro[1])]}
        reporte["vistas"][r["id"]] = vista
        np.savez_compressed(salida / f"clases_{r['id']}.npz", ref=Cr, modelo=Cm)
        lamina(salida / f"lamina_{r['id']}.png", rgb, rgbm, Cr, Cm, f"{r['id']} · yaw {yv} · elev {ajuste['elevacion']} · dist {ajuste['distancia']} · pose {ajuste['clip']}@{ajuste['frac']}")
    (salida / "reporte.json").write_text(json.dumps(reporte, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    return reporte


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifiesto")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--base", default=".")
    a = ap.parse_args()
    man = json.loads(Path(a.manifiesto).read_text(encoding="utf-8"))
    rep = ejecutar(man, Path(a.base), Path(a.salida))
    for k, v in rep["vistas"].items():
        print(k, "IoU", {n: (round(x, 3) if x is not None else None) for n, x in v["iou"].items()})


if __name__ == "__main__":
    main()
