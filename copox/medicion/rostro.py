"""Medición de rostros en estilo ALTH: detecta todas las caras de una imagen
(pares de ojos rodeados de piel), las normaliza a un marco común y mide rasgos.

Marco normalizado: eje u a lo largo de la línea de ojos, v perpendicular hacia
abajo; unidad = ED (distancia entre centros de ojos); origen = punto medio de
los ojos. El parche normalizado mide ``PX`` px por ED.
"""
from __future__ import annotations

import numpy as np

from . import paleta
from .paleta import FONDO, PELO, PIEL, CLARO, OSCURO
from .piezas import componentes

PX = 40                      # px por ED en el parche normalizado
U = (-2.5, 2.5)              # rango horizontal (ED)
V = (-2.6, 2.4)              # rango vertical (ED)


def _anillo_piel(C, c, m=4):
    y0, y1 = max(c['y0'] - m, 0), min(c['y1'] + m, C.shape[0] - 1)
    x0, x1 = max(c['x0'] - m, 0), min(c['x1'] + m, C.shape[1] - 1)
    caja = C[y0:y1 + 1, x0:x1 + 1]
    anillo = np.ones(caja.shape, bool)
    anillo[m:-m or None, m:-m or None] = False
    vec = caja[anillo]
    vec = vec[vec != OSCURO]
    return float(np.mean(np.isin(vec, (PIEL, CLARO)))) if len(vec) else 0.0


def detectar_caras(C: np.ndarray, min_ojo_px: int = 6) -> list[dict]:
    """Pares de ojos en cualquier parte de la imagen. Devuelve lista de dicts con ojo_izq/ojo_der."""
    cs = []
    for c in componentes(C == OSCURO, 25):
        h, w = c['y1'] - c['y0'] + 1, c['x1'] - c['x0'] + 1
        if h < min_ojo_px or w < min_ojo_px or not (0.5 <= h / w <= 2.8):
            continue
        if c['n'] < 0.35 * h * w:  # descarta anillos/marcos (lentes) y trazos
            continue
        if _anillo_piel(C, c) < 0.55:
            continue
        c['h'], c['w'] = h, w
        cs.append(c)
    pares = []
    for i in range(len(cs)):
        for k in range(len(cs)):
            a, b = cs[i], cs[k]
            if a['cx'] >= b['cx']:
                continue
            sim = min(a['n'], b['n']) / max(a['n'], b['n'])
            dx, dy = b['cx'] - a['cx'], abs(b['cy'] - a['cy'])
            wm = max(a['w'], b['w'])
            if sim < 0.45 or dy > 0.6 * max(a['h'], b['h']) or not (1.3 * wm <= dx <= 4.5 * wm):
                continue
            # entre los ojos debe haber piel (puente de la nariz)
            yy = int(round((a['cy'] + b['cy']) / 2))
            seg = C[yy, int(a['x1']) + 1:int(b['x0'])]
            if len(seg) == 0 or np.mean(np.isin(seg, (PIEL, CLARO))) < 0.35:
                continue
            pares.append((sim * (a['n'] + b['n']), i, k))
    usados, caras = set(), []
    for _, i, k in sorted(pares, reverse=True):
        if i in usados or k in usados:
            continue
        usados |= {i, k}
        caras.append({"ojo_izq": cs[i], "ojo_der": cs[k]})
    return caras


def normalizar(C: np.ndarray, rgb: np.ndarray, cara: dict):
    """Parche de clases y RGB en el marco normalizado (vecino más cercano)."""
    a, b = cara["ojo_izq"], cara["ojo_der"]
    c = np.array([(a['cx'] + b['cx']) / 2, (a['cy'] + b['cy']) / 2])
    d = np.array([b['cx'] - a['cx'], b['cy'] - a['cy']])
    ed = float(np.linalg.norm(d))
    eu = d / ed
    ev = np.array([-eu[1], eu[0]])  # perpendicular, hacia abajo en imagen
    us = np.arange(U[0], U[1], 1 / PX) + 0.5 / PX
    vs = np.arange(V[0], V[1], 1 / PX) + 0.5 / PX
    UU, VV = np.meshgrid(us, vs)
    X = c[0] + (UU * eu[0] + VV * ev[0]) * ed
    Y = c[1] + (UU * eu[1] + VV * ev[1]) * ed
    Xi, Yi = np.round(X).astype(int), np.round(Y).astype(int)
    dentro = (Xi >= 0) & (Xi < C.shape[1]) & (Yi >= 0) & (Yi < C.shape[0])
    P = np.zeros(UU.shape, np.uint8)
    R = np.full(UU.shape + (3,), 236, np.uint8)
    P[dentro] = C[Yi[dentro], Xi[dentro]]
    R[dentro] = rgb[Yi[dentro], Xi[dentro]]
    return P, R, {"ed_px": ed, "angulo_grados": float(np.degrees(np.arctan2(d[1], d[0]))), "centro_px": c.tolist()}


def _uv(col, fila):
    return U[0] + (col + 0.5) / PX, V[0] + (fila + 0.5) / PX


def _ix(u=None, v=None):
    return (None if u is None else int((u - U[0]) * PX), None if v is None else int((v - V[0]) * PX))


def medir(P: np.ndarray) -> dict:
    """Rasgos en ED sobre el parche normalizado (ojos en u=±0.5, v=0)."""
    m = {}
    piel, osc, pelo = P == PIEL, P == OSCURO, P == PELO
    # ojos
    ojos = [c for c in componentes(osc, 10)]
    def cerca(u, v, lista, r=0.35):
        out = [c for c in lista if abs(_uv(c['cx'], c['cy'])[0] - u) < r and abs(_uv(c['cx'], c['cy'])[1] - v) < r]
        return max(out, key=lambda c: c['n']) if out else None
    oi, od = cerca(-0.5, 0, ojos), cerca(0.5, 0, ojos)
    if oi and od:
        m["ojo_ancho"] = float(np.mean([(o['x1'] - o['x0'] + 1) / PX for o in (oi, od)]))
        m["ojo_alto"] = float(np.mean([(o['y1'] - o['y0'] + 1) / PX for o in (oi, od)]))
        m["ojo_asimetria"] = float(((oi['x1'] - oi['x0']) - (od['x1'] - od['x0'])) / max(oi['x1'] - oi['x0'], od['x1'] - od['x0'], 1))
        m["ojo_top"] = float(np.mean([_uv(0, o['y0'])[1] for o in (oi, od)]))
    # cejas: oscuro sobre cada ojo, v en [-1.3, -0.15], excluyendo el ojo
    ojo_ids = {(o['y0'], o['x0']) for o in (oi, od) if o}
    cejas = []
    for u0 in (-0.5, 0.5):
        cand = [c for c in ojos if (c['y0'], c['x0']) not in ojo_ids
                and -1.3 < _uv(c['cx'], c['cy'])[1] < -0.12 and abs(_uv(c['cx'], c['cy'])[0] - u0) < 0.45
                and (c['x1'] - c['x0']) > (c['y1'] - c['y0'])]
        if cand:
            cejas.append(max(cand, key=lambda c: c['n']))
    if len(cejas) == 2:
        m["ceja_v"] = float(np.mean([_uv(c['cx'], c['cy'])[1] for c in cejas]))
        m["ceja_ancho"] = float(np.mean([(c['x1'] - c['x0'] + 1) / PX for c in cejas]))
        m["ceja_grosor"] = float(np.mean([c['n'] / (c['x1'] - c['x0'] + 1) / PX for c in cejas]))
        m["ceja_sep"] = float((cejas[1]['x0'] - cejas[0]['x1']) / PX)
    # boca: oscuro centrado bajo los ojos, v en [0.45, 1.7]
    bocas = [c for c in ojos if 0.45 < _uv(c['cx'], c['cy'])[1] < 1.7 and abs(_uv(c['cx'], c['cy'])[0]) < 0.45
             and (c['x1'] - c['x0']) >= 1.5 * (c['y1'] - c['y0'])]
    if bocas:
        b = max(bocas, key=lambda c: c['x1'] - c['x0'])
        m["boca_v"] = float(_uv(b['cx'], b['cy'])[1])
        m["boca_ancho"] = float((b['x1'] - b['x0'] + 1) / PX)
        # curvatura: altura de las comisuras respecto al centro (negativo = comisuras arriba = sonrisa)
        ys, xs = np.nonzero(osc[b['y0']:b['y1'] + 1, b['x0']:b['x1'] + 1])
        if len(xs) > 5:
            xs = xs + b['x0']; ys = ys + b['y0']
            cx = (b['x0'] + b['x1']) / 2
            ext = np.abs(xs - cx) > 0.35 * (b['x1'] - b['x0'])
            cen = np.abs(xs - cx) < 0.15 * (b['x1'] - b['x0'])
            if ext.any() and cen.any():
                m["boca_comisuras"] = float((ys[ext].mean() - ys[cen].mean()) / PX)
    # contorno de cara (piel conectada al eje central)
    def ancho_piel(v):
        _, f = _ix(v=v)
        if f is None or f < 0 or f >= P.shape[0]:
            return None
        fila = piel[f] | (P[f] == OSCURO) | (P[f] == CLARO)
        c0, _ = _ix(u=0)
        if not fila[c0]:
            return None
        izq = c0
        while izq > 0 and fila[izq - 1]:
            izq -= 1
        der = c0
        while der < len(fila) - 1 and fila[der + 1]:
            der += 1
        return (der - izq + 1) / PX
    for v in (0.0, 0.5, 0.9):
        a = ancho_piel(v)
        if a is not None:
            m[f"cara_ancho_v{v:+.1f}"] = a
    # barbilla: primera fila bajo la boca donde la columna central deja de ser cara
    c0, _ = _ix(u=0)
    col = piel[:, c0 - 2:c0 + 3].mean(1) > 0.5
    _, f0 = _ix(v=0.3)
    f = f0
    while f < P.shape[0] - 1 and (col[f] or osc[f, c0 - 2:c0 + 3].any()):
        f += 1
    if f < P.shape[0] - 1:
        m["barbilla_v"] = float(_uv(0, f)[1])
    # línea del pelo: primera fila hacia arriba donde la columna central deja de ser piel
    _, f0 = _ix(v=-0.3)
    f = f0
    while f > 0 and (col[f] or osc[f, c0 - 2:c0 + 3].any()):
        f -= 1
    if f > 0:
        m["frente_v"] = float(_uv(0, f)[1])
        m["frente_es_pelo"] = bool(pelo[f, c0 - 2:c0 + 3].mean() > 0.5)
    return m


def promedio(parches: list[np.ndarray]) -> np.ndarray:
    """Imagen 'frecuencia por clase' del rostro promedio (RGB)."""
    out = np.zeros(parches[0].shape + (3,), float)
    for k, col in paleta.COLORES.items():
        f = np.mean([p == k for p in parches], axis=0)
        out += f[..., None] * np.array(col)
    return np.clip(out, 0, 255).astype(np.uint8)


def es_cara(P: np.ndarray) -> tuple[bool, dict]:
    """Validación sobre el parche normalizado: piel en el núcleo de la cara y ojos de tamaño ALTH."""
    def frac(u0, u1, v0, v1, clases):
        c0, f0 = _ix(u0, v0)
        c1, f1 = _ix(u1, v1)
        z = P[max(f0, 0):f1, max(c0, 0):c1]
        return float(np.isin(z, clases).mean()) if z.size else 0.0
    nucleo = frac(-1.0, 1.0, -0.15, 0.85, (PIEL, OSCURO, CLARO))
    piel_nucleo = frac(-1.0, 1.0, -0.15, 0.85, (PIEL,))
    nariz = frac(-0.25, 0.25, 0.15, 0.55, (PIEL,))
    mejillas = min(frac(-1.0, -0.6, 0.35, 0.8, (PIEL,)), frac(0.6, 1.0, 0.35, 0.8, (PIEL,)))
    m = medir(P)
    ok_ojo = 0.2 <= m.get("ojo_ancho", 0) <= 0.8 and 0.2 <= m.get("ojo_alto", 0) <= 0.95
    info = {"nucleo": nucleo, "piel_nucleo": piel_nucleo, "nariz": nariz, "mejillas": mejillas, "ojo_ok": ok_ojo}
    ok = nucleo >= 0.85 and piel_nucleo >= 0.5 and nariz >= 0.7 and mejillas >= 0.5 and ok_ojo
    return ok, info


def medir_rgb(R: np.ndarray) -> dict:
    """Medición relativa a la piel de ESTA cara (no a la paleta fija), sobre el parche RGB normalizado.
    Rasgo = píxel claramente más oscuro que la piel; contorno = región de color piel conectada al centro."""
    from collections import deque
    R = R.astype(float)
    lum = R @ np.array([0.299, 0.587, 0.114])
    c0, fn0 = _ix(-0.3, 0.2); c1, fn1 = _ix(0.3, 0.55)
    zona = R[fn0:fn1, c0:c1].reshape(-1, 3)
    piel = np.median(zona, 0)
    lp = float(piel @ np.array([0.299, 0.587, 0.114]))
    crom = R / (R.sum(-1, keepdims=True) + 1e-6)
    cp = piel / piel.sum()
    parecido = (np.abs(crom - cp).sum(-1) < 0.06) & (lum > 0.62 * lp) & (lum < 1.35 * lp)
    oscuro = lum < 0.55 * lp
    m = {"piel_rgb": piel.round().tolist()}
    # región de cara conectada desde la nariz
    H, W = parecido.shape
    sc, sf = _ix(0, 0.35)
    vis = np.zeros_like(parecido)
    if parecido[sf, sc]:
        q = deque([(sf, sc)]); vis[sf, sc] = True
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and not vis[yy, xx] and (parecido[yy, xx] or oscuro[yy, xx]) and abs(_uv(xx, yy)[0]) < 2.2:
                    vis[yy, xx] = True; q.append((yy, xx))
    cara = vis
    def ancho(v):
        _, f = _ix(v=v)
        xs = np.nonzero(cara[f])[0]
        if not len(xs):
            return None, None, None
        return (xs.max() - xs.min() + 1) / PX, _uv(xs.min(), 0)[0], _uv(xs.max(), 0)[0]
    for v in (0.0, 0.5, 0.9):
        a, i, d = ancho(v)
        if a is not None:
            m[f"cara_ancho_v{v:+.1f}"] = a
            m[f"cara_simetria_v{v:+.1f}"] = (d + i)  # 0 = simétrica respecto al centro de los ojos
    col = cara[:, sc - 2:sc + 3].any(1)
    filas = np.nonzero(col)[0]
    if len(filas):
        m["barbilla_v"] = float(_uv(0, filas.max())[1])
        m["frente_v"] = float(_uv(0, filas.min())[1])
    # rasgos oscuros dentro (o al borde) de la cara
    rasgos = componentes(oscuro, 6)
    def uv(c):
        return _uv(c['cx'], c['cy'])
    ojos = [c for c in rasgos if abs(abs(uv(c)[0]) - 0.5) < 0.3 and abs(uv(c)[1]) < 0.3]
    oi = max([c for c in ojos if uv(c)[0] < 0], key=lambda c: c['n'], default=None)
    od = max([c for c in ojos if uv(c)[0] > 0], key=lambda c: c['n'], default=None)
    if oi and od:
        m["ojo_ancho"] = float(np.mean([(o['x1'] - o['x0'] + 1) / PX for o in (oi, od)]))
        m["ojo_alto"] = float(np.mean([(o['y1'] - o['y0'] + 1) / PX for o in (oi, od)]))
        m["ojo_asimetria"] = float(((oi['x1'] - oi['x0']) - (od['x1'] - od['x0'])) / max(oi['x1'] - oi['x0'], od['x1'] - od['x0'], 1))
    excl = {id(oi), id(od)}
    cejas = []
    for s in (-1, 1):
        cand = [c for c in rasgos if id(c) not in excl and -1.35 < uv(c)[1] < -0.2 and abs(uv(c)[0] - 0.5 * s) < 0.5
                and (c['x1'] - c['x0']) > 1.5 * (c['y1'] - c['y0'])]
        if cand:
            cejas.append(max(cand, key=lambda c: c['n']))
    if len(cejas) == 2:
        m["ceja_v"] = float(np.mean([uv(c)[1] for c in cejas]))
        m["ceja_ancho"] = float(np.mean([(c['x1'] - c['x0'] + 1) / PX for c in cejas]))
        m["ceja_grosor"] = float(np.mean([c['n'] / (c['x1'] - c['x0'] + 1) / PX for c in cejas]))
        m["ceja_sep"] = float(abs(_uv(cejas[1]['x0'], 0)[0] - _uv(cejas[0]['x1'], 0)[0])) if uv(cejas[0])[0] < uv(cejas[1])[0] else None
        # inclinación: diferencia de altura entre extremo interno y externo (positivo = ceño)
    bocas = [c for c in rasgos if id(c) not in excl and 0.45 < uv(c)[1] < 1.6 and abs(uv(c)[0]) < 0.4 and (c['x1'] - c['x0']) >= 2 * (c['y1'] - c['y0'])]
    if bocas:
        b = max(bocas, key=lambda c: c['x1'] - c['x0'])
        m["boca_v"] = float(uv(b)[1]); m["boca_ancho"] = float((b['x1'] - b['x0'] + 1) / PX)
        ys, xs = np.nonzero(oscuro[b['y0']:b['y1'] + 1, b['x0']:b['x1'] + 1])
        xs = xs + b['x0']; ys = ys + b['y0']; cx = (b['x0'] + b['x1']) / 2; wb = b['x1'] - b['x0']
        ext, cen = np.abs(xs - cx) > 0.35 * wb, np.abs(xs - cx) < 0.15 * wb
        if ext.any() and cen.any():
            m["boca_comisuras"] = float((ys[ext].mean() - ys[cen].mean()) / PX)
    return m


def es_cara_rgb(m: dict) -> bool:
    """Filtro de plausibilidad de una cara ALTH sobre las medidas relativas a la piel."""
    a0, a5 = m.get("cara_ancho_v+0.0"), m.get("cara_ancho_v+0.5")
    return (a0 is not None and a5 is not None and 1.3 <= a0 <= 3.4 and 1.2 <= a5 <= 3.4
            and 0.6 <= m.get("barbilla_v", 0) <= 1.9 and "ojo_ancho" in m and 0.2 <= m["ojo_ancho"] <= 0.8)


def rasgos_por_perfiles(R: np.ndarray) -> dict:
    """Propone rasgos con perfiles de luminosidad relativos a la piel de la cara (para verificación humana).
    Devuelve posiciones en ED en el marco normalizado (ojos en u=±0.5, v=0)."""
    R = R.astype(float)
    L = R @ np.array([0.299, 0.587, 0.114])
    def fila(v):
        return int((v - V[0]) * PX)
    def colu(u):
        return int((u - U[0]) * PX)
    zonas = [L[fila(0.25):fila(0.55), colu(-0.85):colu(-0.5)], L[fila(0.25):fila(0.55), colu(0.5):colu(0.85)]]
    lp = float(np.median(np.concatenate([z.ravel() for z in zonas])))
    piel = np.median(np.concatenate([R[fila(0.25):fila(0.55), colu(-0.85):colu(-0.5)].reshape(-1, 3), R[fila(0.25):fila(0.55), colu(0.5):colu(0.85)].reshape(-1, 3)]), 0)
    crom = R / (R.sum(-1, keepdims=True) + 1e-6)
    es_piel = (np.abs(crom - piel / piel.sum()).sum(-1) < 0.07) & (L > 0.6 * lp)
    m = {}
    c = L[:, colu(-0.12):colu(0.12)].mean(1)
    vv = (np.arange(len(c)) + 0.5) / PX + V[0]
    def rango(a, b):
        return (vv >= a) & (vv <= b)
    # boca: mínimo del perfil central entre 0.35 y 1.0
    r = rango(0.35, 1.05)
    i = np.argmin(np.where(r, c, np.inf))
    if c[i] < 0.8 * lp:
        m["boca_v"] = float(vv[i])
        row = L[i]
        x0 = colu(0)
        izq = x0
        while izq > 0 and row[izq - 1] < 0.85 * lp:
            izq -= 1
        der = x0
        while der < len(row) - 1 and row[der + 1] < 0.85 * lp:
            der += 1
        m["boca_ancho"] = (der - izq + 1) / PX
    # base de la nariz: banda más oscura entre 0.15 y (boca - 0.08)
    tope = m.get("boca_v", 0.9) - 0.08
    r = rango(0.12, tope)
    if r.any():
        i = np.argmin(np.where(r, c, np.inf))
        if c[i] < 0.93 * lp:
            m["nariz_base_v"] = float(vv[i])
    # barbilla: primera fila bajo la boca donde la columna central deja de ser piel (3 filas seguidas)
    pc = es_piel[:, colu(-0.12):colu(0.12)].mean(1) > 0.5
    ini = fila(m.get("boca_v", 0.6) + 0.12)
    for f in range(ini, len(pc) - 3):
        if not pc[f] and not pc[f + 1] and not pc[f + 2]:
            m["barbilla_v"] = float(vv[f]); break
    # línea del pelo (centro): primera fila sobre los ojos que deja de ser piel
    for f in range(fila(-0.35), 2, -1):
        if not pc[f] and not pc[f - 1] and not pc[f - 2]:
            m["pelo_v"] = float(vv[f]); break
    # cejas: banda oscura sobre cada ojo
    cejas = []
    for s in (-1, 1):
        cc = L[:, colu(0.5 * s - 0.2):colu(0.5 * s + 0.2)].mean(1)
        r = rango(-1.05, -0.2)
        i = np.argmin(np.where(r, cc, np.inf))
        if cc[i] < 0.7 * lp:
            k0 = i
            while k0 > 0 and cc[k0 - 1] < 0.8 * lp:
                k0 -= 1
            k1 = i
            while k1 < len(cc) - 1 and cc[k1 + 1] < 0.8 * lp and vv[k1 + 1] < -0.15:
                k1 += 1
            cejas.append((float(vv[i]), (k1 - k0 + 1) / PX))
    if len(cejas) == 2:
        m["ceja_v"] = float(np.mean([x[0] for x in cejas]))
        m["ceja_grosor"] = float(np.mean([x[1] for x in cejas]))
    # anchos de cara (piel conectada desde el centro de la fila)
    for v in (0.0, 0.5, 0.8):
        f = fila(v); row = es_piel[f] | (L[f] < 0.8 * lp)
        x0 = colu(0) if v > 0 else colu(0)
        if not es_piel[f, colu(-0.1):colu(0.1)].any() and v == 0.0:
            x0 = colu(0)
        izq = der = x0
        while izq > 0 and row[izq - 1]:
            izq -= 1
        while der < len(row) - 1 and row[der + 1]:
            der += 1
        m[f"cara_izq_v{v:+.1f}"] = float(U[0] + izq / PX)
        m[f"cara_der_v{v:+.1f}"] = float(U[0] + (der + 1) / PX)
    m["piel_lum"] = lp
    return m
