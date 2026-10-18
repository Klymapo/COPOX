"""Rostro en el marco normalizado de SENKU (copox.medicion.rostro).

El modelo se renderiza de frente con los ojos en u = ±0.5 ED, v = 0 y 40 px/ED,
el mismo marco de los parches de referencia (R_*.png / P_*.npy). Así la cara del
modelo y las de las referencias se superponen y se miden con la misma regla.
"""
from __future__ import annotations

import datetime as _dt

import numpy as np

from ..medicion import rostro as senku
from . import modos
from .lamina import _armar, diferencia
from .vistas import leer

TAM = int(round((senku.U[1] - senku.U[0]) * senku.PX))  # 200 px
CENTRO = (-senku.U[0] * senku.PX, -senku.V[0] * senku.PX)  # píxel del punto medio de los ojos


def ojos_px(ses, res) -> list:
    """Centro (x, y) en píxeles de cada ojo: centroide de los píxeles visibles de las placas de ojo."""
    out = []
    pr = np.where(res.tri >= 0, ses.prim[np.maximum(res.tri, 0)], -1)
    for k, n in enumerate(ses.mat_nombre):
        if "eye" in n.lower():
            ys, xs = np.nonzero(pr == k)
            if len(xs):
                out.append((xs.mean() + 0.5, ys.mean() + 0.5))
    return sorted(out)


def render_rostro(ses, codigo: str = "cara_frente", autor: str = "elio", tam_aux: int = 400):
    """Render en el marco SENKU (200×200). Devuelve (resultado, info)."""
    v = leer(codigo)
    base = ses.render(f"{codigo};modo=clases;tam={tam_aux}", autor)
    oj = ojos_px(ses, base)
    if len(oj) != 2:
        raise ValueError(f"Se esperaban 2 ojos y hay {len(oj)}")
    (x0, y0), (x1, y1) = oj
    ed_px = float(np.hypot(x1 - x0, y1 - y0))
    f = senku.PX / ed_px
    esc = base.escala * f
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    # punto del plano (unidades) que cae en el centro de los ojos
    ux, uy = (mx - base.centro[0]) / base.escala, (base.centro[1] - my) / base.escala
    cen = (CENTRO[0] - ux * esc, CENTRO[1] + uy * esc)
    r = ses.render(f"{codigo};tam={TAM}", autor, fijar=(esc, cen))
    rc = r if v.modo in ("clases", "clases_tri") else ses.render(f"{codigo};modo=clases;tam={TAM}", autor, fijar=(esc, cen))
    return r, {"clases": rc.clases, "ed_unidades": ed_px / base.escala, "inclinacion_px": y1 - y0}


def tabla(medidas: dict, canon: dict) -> str:
    claves = [("ceja_v", "ceja_centro_v"), ("ceja_grosor", "ceja_grosor"), ("ojo_ancho", "ojo_ancho"),
              ("ojo_alto", "ojo_alto"), ("boca_v", "boca_v"), ("boca_ancho", "boca_ancho"),
              ("barbilla_v", "barbilla_v"), ("cara_ancho_v+0.5", "cara_ancho_v0.5"), ("cara_ancho_v+0.9", "cara_ancho_v0.8")]
    partes = []
    for km, kc in claves:
        a, b = medidas.get(km), canon.get(kc)
        if a is None and b is None:
            continue
        sa = "—" if a is None else f"{a:.2f}"
        sb = "—" if b is None else f"{b:.2f}"
        partes.append(f"{km} {sa}/{sb}")
    return "modelo/canon (ED): " + " · ".join(partes)


def lamina_rostro(ses, ref_rgb: np.ndarray, ref_clases: np.ndarray, canon: dict, codigo: str = "cara_frente",
                  autor: str = "elio", nombre_ref: str = "ref"):
    """Referencia normalizada | modelo | superposición | diferencia de clases, con medidas SENKU."""
    r, info = render_rostro(ses, codigo, autor)
    m = senku.medir(info["clases"])
    sup = (0.5 * ref_rgb[..., :3] + 0.5 * r.imagen).astype(np.uint8)
    esc = 2  # paneles a 400 px para leerlos
    big = [np.repeat(np.repeat(p, esc, 0), esc, 1) for p in
           (ref_rgb[..., :3].astype(np.uint8), r.imagen, sup, diferencia(ref_clases, info["clases"]))]
    fecha = _dt.date.today().isoformat()
    sello = f"{ses.nombre} · {ses.hash[:8]} · rostro SENKU · {nombre_ref} · {autor} · {fecha}"
    img = _armar(big, [nombre_ref, f"modelo ({r.vista.modo})", "superposición", "diferencia (rojo=modelo, azul=ref)"],
                 tabla(m, canon), sello, r.codigo)
    return img, {"medidas": m, "ed_unidades": info["ed_unidades"]}
