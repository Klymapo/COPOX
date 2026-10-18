"""Láminas de comparación: referencia | modelo | superposición | diferencia.

    lamina_ref(sesion, "frente", "Hoja.png", recorte=(x0, y0, x1, y1))
    lamina_ab(sesion_a, sesion_b, "cara_34;modo=arcilla")

Diferencia por clases (paleta ALTH): gris = coincide; rojo = solo modelo/B;
azul = solo referencia/A; amarillo = ambos con clase distinta.
"""
from __future__ import annotations

import datetime as _dt

import numpy as np
from PIL import Image

from ..medicion import paleta
from ..medicion.piezas import iou_por_clase
from . import modos
from .vistas import leer

GRUPOS = {"silueta": [1, 2, 3, 4, 5], "sin_pelo": [2, 3, 4, 5], "pelo": [1], "piel": [2],
          "claro": [3], "oscuro": [4], "azul": [5]}


def _caja(C, sin_pelo=False):
    ys, xs = np.nonzero((C > 1) if sin_pelo else (C > 0))
    return xs.min(), xs.max(), ys.min(), ys.max()


def diferencia(Ca, Cb) -> np.ndarray:
    D = np.tile(np.array(modos.FONDO * 255, np.uint8), Ca.shape + (1,))
    a, b = Ca > 0, Cb > 0
    D[a & b & (Ca == Cb)] = (150, 150, 150)
    D[a & b & (Ca != Cb)] = (235, 190, 40)
    D[b & ~a] = (215, 50, 40)
    D[a & ~b] = (40, 90, 215)
    return D


def _texto(numeros: dict) -> str:
    return "IoU " + " · ".join(f"{k} {v:.3f}" for k, v in numeros.items() if v is not None)


def _armar(paneles, titulos, linea, sello, codigo):
    from PIL import ImageDraw
    T = paneles[0].shape[0]
    t = max(12, T // 34)
    cab = int(t * 1.6)
    out = Image.new("RGB", (T * len(paneles), T + cab * 2), (24, 26, 32))
    d = ImageDraw.Draw(out)
    f = modos._fuente(t)
    for i, (p, ti) in enumerate(zip(paneles, titulos)):
        out.paste(Image.fromarray(p), (i * T, cab))
        d.text((i * T + 6, 3), ti, fill=(235, 235, 235), font=f)
    d.text((6, T + cab + 3), linea, fill=(235, 235, 235), font=f)
    return modos.sellar(np.asarray(out), sello, codigo, t)


def cargar_ref(ruta: str, recorte=None, tam: int = 512):
    """Recorta, rellena a cuadrado con el fondo ALTH y escala a tam. Devuelve (rgb, clases)."""
    im = Image.open(ruta).convert("RGB")
    if recorte:
        im = im.crop(tuple(recorte))
    w, h = im.size
    L = max(w, h)
    lienzo = Image.new("RGB", (L, L), tuple(int(x) for x in paleta.COLORES[0]))
    lienzo.paste(im, ((L - w) // 2, (L - h) // 2))
    rgb = np.asarray(lienzo.resize((tam, tam), Image.LANCZOS))
    return rgb, paleta.segmentar_referencia(rgb)


def lamina_ref(ses, codigo: str, ref: str, recorte=None, autor: str = "elio", ancla: str = "ojos"):
    """Ajusta escala y posición del modelo a la silueta de la referencia y compara.
    ancla: 'ojos' (línea de ojos → suela; por defecto, cae a 'alto' si no detecta ojos),
    'alto' (silueta completa), 'sin_pelo' o 'ancho'."""
    v = leer(codigo)
    rgb, Cr = cargar_ref(ref, recorte, v.tam)
    base = ses.render(f"{codigo};modo=clases", autor)
    from ..medicion.piezas import ojos as _ojos
    mx0, mx1, my0, my1 = _caja(base.clases)
    rx0, rx1, ry0, ry1 = _caja(Cr)
    ref_ojos = _ojos(Cr) if ancla == "ojos" else []
    mod_ojos = ses.ojos_3d(v.clip, v.t) if ancla == "ojos" else []
    if len(ref_ojos) == 2 and len(mod_ojos) == 2:
        # ojos → suela: escala por esa altura; alinea el centro de los ojos y la suela
        x, y, _ = base.cam.proyectar(np.array(mod_ojos))
        mox, moy = base.centro[0] + x.mean() * base.escala, base.centro[1] - y.mean() * base.escala
        rox, roy = np.mean([o["cx"] for o in ref_ojos]), np.mean([o["cy"] for o in ref_ojos])
        f = (ry1 + 0.5 - roy) / max(my1 + 0.5 - moy, 1)
        ax_m, ax_r = mox, rox
        usado = "ojos"
    else:
        sp = ancla == "sin_pelo"
        if sp:
            mx0, mx1, my0, my1 = _caja(base.clases, True)
            rx0, rx1, ry0, ry1 = _caja(Cr, True)
        f = (rx1 - rx0) / max(mx1 - mx0, 1) if ancla == "ancho" else (ry1 - ry0) / max(my1 - my0, 1)
        ax_m, ax_r = (mx0 + mx1 + 1) / 2, (rx0 + rx1 + 1) / 2
        usado = "alto" if ancla == "ojos" else ancla
    esc = base.escala * f
    y_bajo = (base.centro[1] - (my1 + 0.5)) / base.escala
    x_med = (ax_m - base.centro[0]) / base.escala
    cen = (ax_r - x_med * esc, (ry1 + 0.5) + y_bajo * esc)
    rc = ses.render(f"{codigo};modo=clases", autor, fijar=(esc, cen))
    rm = ses.render(codigo, autor, fijar=(esc, cen)) if v.modo not in ("clases", "clases_tri") else rc
    sup = (0.5 * rgb + 0.5 * rm.imagen).astype(np.uint8)
    iou = iou_por_clase(Cr, rc.clases, GRUPOS)
    fecha = _dt.date.today().isoformat()
    sello = f"{ses.nombre} · {ses.hash[:8]} · {v.nombre} · lámina ref · {v.tam}px · {autor} · {fecha}"
    img = _armar([rgb, rm.imagen, sup, diferencia(Cr, rc.clases)],
                 ["referencia", f"modelo ({v.modo})", "superposición", "diferencia (rojo=modelo, azul=ref)"],
                 _texto(iou) + f"   (ancla: {usado})", sello, f"{rm.codigo};ref={ref.split('/')[-1]};recorte={recorte}")
    return img, {"iou": iou, "escala": esc, "centro": cen, "codigo": rm.codigo, "ancla": usado}


def lamina_ab(ses_a, ses_b, codigo: str, autor: str = "elio"):
    """Misma toma y mismo encuadre para dos versiones."""
    v = leer(codigo)
    ra = ses_a.render(codigo, autor)
    fij = (ra.escala, ra.centro)
    rb = ses_b.render(codigo, autor, fijar=fij)
    ca = ra if v.modo in ("clases", "clases_tri") else ses_a.render(f"{codigo};modo=clases", autor, fijar=fij)
    cb = rb if v.modo in ("clases", "clases_tri") else ses_b.render(f"{codigo};modo=clases", autor, fijar=fij)
    sup = (0.5 * ra.imagen + 0.5 * rb.imagen).astype(np.uint8)
    iou = iou_por_clase(ca.clases, cb.clases, GRUPOS)
    fecha = _dt.date.today().isoformat()
    sello = (f"A {ses_a.nombre} {ses_a.hash[:8]} | B {ses_b.nombre} {ses_b.hash[:8]} · {v.nombre} · "
             f"A/B · {v.tam}px · {autor} · {fecha}")
    img = _armar([ra.imagen, rb.imagen, sup, diferencia(ca.clases, cb.clases)],
                 [f"A {ses_a.nombre}", f"B {ses_b.nombre}", "superposición", "diferencia (rojo=B, azul=A)"],
                 _texto(iou), sello, ra.codigo)
    return img, {"iou": iou, "codigo": ra.codigo}
