"""Armas PROVISIONALES estilo ALTH-META para probar agarres de Adán: florete y pistola tipo Glock.

python -m copox.armas.armas_alth SALIDA_DIR

Estilo: piezas convexas con chaflán (low-poly suave), sombreado plano con normales por cara, colores de
spec/alth_spec.json → paleta. Escala de objetos de mano chibi: la empuñadura mide lo que la palma de Adán
(ancho de palma 0.066 u ≈ 8.5 cm reales → 0.78 u/m para lo que toca la mano); hojas y cañones se acortan
a proporción chibi (el florete mide ≈ 54 % del alto de Adán, como las armas de las referencias).

Ejes de cada arma (unidades de Godot, 1 u = alto de Adán / 0.848):
  x = hacia adelante (cañón / hoja), y = arriba, z = lado.
  Nodo "AGARRE": centro de la empuñadura; su eje +y corre a lo largo de la empuñadura (de meñique a índice).
"""
from __future__ import annotations

import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import ConvexHull


def hex2lin(h):
    c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# --- piezas -------------------------------------------------------------------------
def casco(P):
    """Envolvente convexa → triángulos con normales hacia afuera."""
    P = np.asarray(P, float)
    h = ConvexHull(P)
    F = h.simplices.copy()
    c = P.mean(0)
    T = P[F]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    flip = (n * (T.mean(1) - c)).sum(1) < 0
    F[flip] = F[flip][:, ::-1]
    return P, F


def caja(x0, x1, y0, y1, z0, z1, b):
    """Caja con chaflán b en todas las aristas (24 puntos)."""
    pts = []
    for x, sx in ((x0, 1), (x1, -1)):
        for y, sy in ((y0, 1), (y1, -1)):
            for z, sz in ((z0, 1), (z1, -1)):
                pts += [(x + sx * b, y, z), (x, y + sy * b, z), (x, y, z + sz * b)]
                pts += [(x + sx * b, y + sy * b * 0.3, z + sz * b * 0.3)]
    return casco(pts)


def caja_inclinada(abajo, arriba, z, b):
    """Prisma entre dos rectángulos en x-y (abajo y arriba: (x0, x1, y)), grosor ±z, con chaflán."""
    pts = []
    for (x0, x1, y), sy in ((abajo, 1), (arriba, -1)):
        for x, sx in ((x0, 1), (x1, -1)):
            for zz, sz in ((-z, 1), (z, -1)):
                pts += [(x + sx * b, y, zz), (x, y + sy * b, zz), (x, y, zz + sz * b)]
    return casco(pts)


def anillos(eje_x, radios, lados=8, rot=np.pi / 8):
    """Sólido de revolución facetado alrededor del eje x: lista de (x, r)."""
    pts = []
    for x, r in zip(eje_x, radios):
        for k in range(lados):
            a = rot + 2 * np.pi * k / lados
            pts.append((x, r * np.cos(a), r * np.sin(a)))
    return casco(pts)


def mover(PF, d=(0, 0, 0), R=None):
    P, F = PF
    if R is not None:
        P = P @ np.asarray(R).T
    return P + np.asarray(d), F


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# --- armas --------------------------------------------------------------------------
PAL = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "spec", "alth_spec.json")))["paleta"]


def glock():
    negro, negro2, oscuro = PAL["negro_calido"][2], PAL["negro_calido"][3], PAL["negro_calido"][4]
    metal = PAL["metal"][3]
    piezas = [
        ("corredera", negro, caja(-0.060, 0.066, 0.034, 0.066, -0.0165, 0.0165, 0.0055)),
        ("armazon", negro2, caja(-0.052, 0.060, 0.018, 0.037, -0.0145, 0.0145, 0.004)),
        # empuñadura inclinada 18° hacia atrás
        ("empunadura", negro2, caja_inclinada((-0.083, -0.040, -0.052), (-0.058, -0.016, 0.022), 0.0160, 0.0050)),
        ("base_cargador", oscuro, caja_inclinada((-0.086, -0.040, -0.058), (-0.085, -0.040, -0.050), 0.0170, 0.0020)),
        # guardamonte: barra de abajo y barra de enfrente
        ("guardamonte_abajo", negro2, caja(-0.020, 0.016, -0.002, 0.005, -0.0045, 0.0045, 0.0018)),
        ("guardamonte_frente", negro2, mover(caja(-0.003, 0.004, -0.002, 0.024, -0.0045, 0.0045, 0.0015), (0.012, 0, 0), rot_z(0.20))),
        ("gatillo", metal, mover(caja(-0.0025, 0.0025, 0.004, 0.020, -0.0028, 0.0028, 0.0010), (-0.004, 0, 0), rot_z(-0.25))),
        ("mira_atras", oscuro, caja(-0.056, -0.046, 0.065, 0.071, -0.0080, 0.0080, 0.0015)),
        ("mira_frente", oscuro, caja(0.054, 0.060, 0.065, 0.070, -0.0030, 0.0030, 0.0012)),
        ("boca", oscuro, mover(anillos([0.0655, 0.0668], [0.0062, 0.0052], 8), (0, 0.052, 0))),
        ("expulsion", oscuro, caja(0.000, 0.022, 0.0648, 0.0666, -0.0060, 0.0100, 0.0010)),
    ]
    for k, x in enumerate((-0.050, -0.044, -0.038)):    # estrías de la corredera (relieve)
        piezas.append((f"estria_{k}", oscuro, caja(x, x + 0.003, 0.038, 0.062, -0.0172, 0.0172, 0.0008)))
    # agarre: centro de la empuñadura; +y a lo largo de la empuñadura (inclinada 18° hacia atrás)
    agarre = {"translation": [-0.052, -0.012, 0.0], "rotation": _q_z(np.radians(18))}
    return piezas, agarre


def florete():
    oro, oro2 = PAL["oro_envejecido"][2], PAL["oro_envejecido"][3]
    cuero = PAL["marron_calido"][3]
    hoja, hoja2 = PAL["metal"][1], PAL["metal"][2]
    L = 0.36
    x_hoja = np.array([0.026, 0.06, L * 0.6, L])
    piezas = [
        ("pomo", oro2, anillos([-0.098, -0.094, -0.086, -0.080], [0.0060, 0.0120, 0.0120, 0.0070], 8)),
        ("empunadura", cuero, anillos([-0.080, -0.044, -0.008], [0.0078, 0.0092, 0.0082], 8)),
        ("virola", oro, anillos([-0.010, -0.002], [0.0098, 0.0098], 8)),
        # cazoleta (campana) facetada
        ("cazoleta", oro, anillos([0.000, 0.006, 0.014, 0.020, 0.024], [0.010, 0.036, 0.034, 0.024, 0.010], 12, 0)),
        ("ricasso", hoja2, anillos([0.022, 0.032], [0.0060, 0.0058], 4, np.pi / 4)),
        # hoja cuadrada (rombo) que se afila; el último tramo casi punta
        ("hoja", hoja, anillos(x_hoja, [0.0080, 0.0072, 0.0055, 0.0030], 4, np.pi / 4)),
        ("boton", hoja2, anillos([L - 0.004, L + 0.003, L + 0.008], [0.0040, 0.0060, 0.0035], 8)),
    ]
    for k, x in enumerate((-0.070, -0.056, -0.042, -0.028)):     # anillos del cuero (alambre dorado)
        piezas.append((f"alambre_{k}", oro2, anillos([x, x + 0.003], [0.0094, 0.0094], 8)))
    # agarre: centro del puño; +y del agarre a lo largo de la hoja (en el florete la empuñadura y la hoja son colineales)
    agarre = {"translation": [-0.044, 0.0, 0.0], "rotation": _q_z(-np.pi / 2)}
    return piezas, agarre


def _q_z(a):
    return [0.0, 0.0, float(np.sin(a / 2)), float(np.cos(a / 2))]


# --- GLB -------------------------------------------------------------------------------
def escribir_glb(ruta, nombre, piezas, agarre):
    bin_ = bytearray()
    j = {"asset": {"version": "2.0", "generator": "COPOX armas_alth (PROVISIONAL)"}, "scene": 0,
         "scenes": [{"nodes": [0]}], "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": []}
    mats = {}

    def add(arr, typ, comp=5126, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        while len(bin_) % 4:
            bin_.append(0)
        bv = {"buffer": 0, "byteOffset": len(bin_), "byteLength": arr.nbytes}
        if target:
            bv["target"] = target
        bin_.extend(arr.tobytes()); j["bufferViews"].append(bv)
        a = {"bufferView": len(j["bufferViews"]) - 1, "componentType": comp, "count": len(arr), "type": typ}
        if minmax:
            a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
        j["accessors"].append(a)
        return len(j["accessors"]) - 1

    prims = []
    rng = np.random.default_rng(7)
    for nom, color, (P, F) in piezas:
        if color not in mats:
            mats[color] = len(j["materials"])
            j["materials"].append({"name": f"ALTH_{color[1:]}", "pbrMetallicRoughness": {
                "baseColorFactor": hex2lin(color).tolist() + [1.0], "metallicFactor": 0.0, "roughnessFactor": 0.85}})
        T = P[F]
        N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); N /= np.linalg.norm(N, axis=1, keepdims=True)
        V = T.reshape(-1, 3).astype(np.float32)
        Nv = np.repeat(N, 3, 0).astype(np.float32)
        # variación leve por cara (estándar ALTH: sombreado plano con variación)
        var = np.repeat(1 + rng.uniform(-0.035, 0.035, len(F)), 3)[:, None]
        C = np.concatenate([np.clip(var, 0, 1.2) * np.ones((len(V), 3)), np.ones((len(V), 1))], 1).astype(np.float32)
        I = np.arange(len(V), dtype=np.uint32)
        prims.append({"attributes": {"POSITION": add(V, "VEC3", target=34962, minmax=True),
                                     "NORMAL": add(Nv, "VEC3", target=34962),
                                     "COLOR_0": add(np.clip(C, 0, 1), "VEC4", target=34962)},
                      "indices": add(I, "SCALAR", 5125, 34963), "material": mats[color]})
    j["meshes"].append({"name": nombre, "primitives": prims})
    j["nodes"] = [{"name": nombre, "children": [1, 2]},
                  {"name": nombre + "_malla", "mesh": 0},
                  {"name": "AGARRE", **agarre}]
    j["buffers"] = [{"byteLength": len(bin_)}]
    while len(bin_) % 4:
        bin_.append(0)
    js = json.dumps(j, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4)
    with open(ruta, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942)); f.write(bin_)
    return sum(len(F) for _, _, (P, F) in piezas)


def main(salida):
    os.makedirs(salida, exist_ok=True)
    for nombre, fn in (("FLORETE_ALTH_PROVISIONAL", florete), ("PISTOLA_ALTH_PROVISIONAL", glock)):
        piezas, agarre = fn()
        tris = escribir_glb(os.path.join(salida, nombre + ".glb"), nombre, piezas, agarre)
        print(nombre, "triángulos:", tris)


if __name__ == "__main__":
    main(sys.argv[1])
