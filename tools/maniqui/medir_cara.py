"""Mide la cabeza y los rasgos de una referencia ALTH (solo numpy + scipy + Pillow, sin IA) y escribe un JSON
de proporciones relativas al ANCHO DE LA CARA, que es lo que consume cabeza.py.

Uso: medir_cara.py referencia.jpg salida.json [--recorte x0,y0,x1,y1] [--vista frente|lado] [--debug out.png]
     Varias vistas: se corre una vez por vista y cabeza.py combina los JSON (frente = posiciones, lado = profundidad).

Qué mide (frente): caja de la cara (piel), llenado de la caja (qué tan "cajón" es la cabeza), radio de esquina,
ojos (manchas oscuras dentro de la piel: centro, ancho, alto), cejas, boca, nariz (si hay sombra), ancho de mandíbula.
Qué mide (lado): fondo de la cabeza vs alto de la cara, qué tan plano es el frente, posición de la oreja.
Límites: es un dibujo; lo que el pelo tapa no se mide (la coronilla sale de la proporción alto/ancho del estilo).
"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage

def srgb_a_lab(rgb):
    c = rgb / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def mayor(mask):
    et, n = ndimage.label(mask)
    if not n: return mask
    t = ndimage.sum(mask, et, range(1, n + 1)); return et == (1 + int(np.argmax(t)))

def caja(m):
    ys, xs = np.where(m); return xs.min(), ys.min(), xs.max(), ys.max()

def medir(rgb, vista):
    lab = srgb_a_lab(rgb); L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    piel = (L > 45) & (a > 10) & (b > 8) & (a >= 0.36 * b) & (a < b * 1.6 + 8)   # a>9: el pelo rubio tiene a≈6; piel ≥11 (medido en Theo)
    piel = ndimage.binary_opening(piel, iterations=2)
    et, n = ndimage.label(piel)                                  # fuera motas: solo manchas de al menos 2 % de la mayor
    if n:
        t = ndimage.sum(piel, et, range(1, n + 1)); piel = np.isin(et, 1 + np.where(t >= 0.02 * t.max())[0])
    # cierre grande (2.5 % del lado) para que lentes, cejas y boca no partan la cara en pedazos; luego la mancha mayor
    r = max(6, int(0.025 * min(rgb.shape[:2])))
    dil = ndimage.distance_transform_edt(~piel) <= r
    cerrada = ndimage.distance_transform_edt(dil) > r                  # dilatar r y erosionar r = cierre con disco
    cara_llena = ndimage.binary_fill_holes(mayor(cerrada))
    cara = piel & cara_llena
    x0, y0, x1, y1 = caja(cara_llena)
    # cortar el cuello: de abajo hacia arriba, la primera fila que mide al menos 60 % del ancho típico es la barbilla
    filas_w = cara_llena[y0:y1 + 1].sum(1); tipico = np.percentile(filas_w, 60)
    desde_abajo = np.where(filas_w[::-1] >= 0.6 * tipico)[0]
    if len(desde_abajo): y1 = y1 - int(desde_abajo[0]); cara_llena[y1 + 1:] = False; cara[y1 + 1:] = False
    x0, y0, x1, y1 = caja(cara_llena); H = y1 - y0 + 1
    filas_w = cara_llena[y0:y1 + 1].sum(1)
    W = int(np.percentile(filas_w[H // 4: 3 * H // 4], 40))        # ancho de la cara sin orejas
    out = {'vista': vista, 'px': {'cara': [int(x0), int(y0), int(x1), int(y1)], 'ancho_cara': W}}
    out['orejas_sobresalen'] = float((filas_w.max() - W) / W / 2)   # cuánto sale cada oreja respecto al ancho de cara
    anchos = filas_w / W
    out['llenado_caja'] = float(np.clip(anchos, 0, 1).mean())
    out['ancho_arriba'] = float(np.median(anchos[: max(3, H // 10)]))
    out['ancho_medio'] = float(np.median(anchos[H // 3: 2 * H // 3]))
    out['ancho_abajo'] = float(np.median(anchos[-max(3, H // 10):]))        # mandíbula vs ancho de cara
    # radio de esquina inferior: a qué distancia del borde inferior la fila ya llena el 95 % del ancho
    k = int(np.argmax(anchos[::-1] > 0.95 * out['ancho_medio'])); out['radio_esquina_abajo'] = k / W
    if vista == 'lado':
        out['fondo_sobre_alto'] = W / H
        # frente plano: desviación del borde frontal (columna mínima/máxima según orientación) respecto a una recta
        filas = np.arange(y0, y1 + 1); izq = np.array([np.where(cara_llena[y])[0].min() for y in filas]); der = np.array([np.where(cara_llena[y])[0].max() for y in filas])
        lado_frente = izq if (izq.std() < der.std()) else der
        out['frente_plano_desv'] = float(lado_frente.std() / W)
        return out
    # rasgos: oscuro dentro de la cara (ojos, lentes, cejas, boca)
    oscuro = (L < 42) & cara_llena
    et, n = ndimage.label(oscuro); comps = []
    for i in range(1, n + 1):
        m = et == i; A = m.sum()
        if A < 0.0002 * W * H: continue
        cx0, cy0, cx1, cy1 = caja(m); comps.append({'cx': (cx0 + cx1) / 2, 'cy': (cy0 + cy1) / 2, 'w': cx1 - cx0 + 1, 'h': cy1 - cy0 + 1, 'area': int(A)})
    xc = (x0 + x1) / 2
    # ojos: el par más grande y simétrico respecto al centro de la cara, en la mitad superior
    cand = [c for c in comps if c['cy'] < y0 + 0.7 * H and c['h'] > 0.04 * H]
    mejor = None
    for i, p in enumerate(cand):
        for q in cand[i + 1:]:
            if (p['cx'] - xc) * (q['cx'] - xc) < 0 and abs(p['cy'] - q['cy']) < 0.08 * H and abs(p['area'] - q['area']) < 0.6 * max(p['area'], q['area']):
                s = p['area'] + q['area']
                if mejor is None or s > mejor[0]: mejor = (s, p, q)
    rel = lambda v: round(float(v) / W, 4)
    if mejor:
        _, p, q = mejor; p, q = sorted([p, q], key=lambda c: c['cx'])
        out['ojos'] = {'separacion': rel(q['cx'] - p['cx']), 'ancho': rel((p['w'] + q['w']) / 2), 'alto': rel((p['h'] + q['h']) / 2),
                       'y_desde_arriba': rel((p['cy'] + q['cy']) / 2 - y0), 'y_sobre_barbilla': rel(y1 - (p['cy'] + q['cy']) / 2), 'y_rel_alto': round(float(((p['cy'] + q['cy']) / 2 - y0) / H), 4)}
        ye = (p['cy'] + q['cy']) / 2
        # cejas: oscuro (café/negro) justo arriba de cada ojo
        cejas = [c for c in comps if c['cy'] < ye - 0.5 * p['h'] and c['cy'] > ye - 2.5 * p['h'] and c['w'] > 0.5 * p['w'] and c not in (p, q)]
        if cejas: out['cejas'] = {'y_sobre_ojo': rel(ye - np.mean([c['cy'] for c in cejas])), 'ancho': rel(np.mean([c['w'] for c in cejas])), 'alto': rel(np.mean([c['h'] for c in cejas]))}
        # boca: oscuro bajo los ojos, cerca del centro, más ancho que alto
        # la boca suele ser una línea delgada y menos oscura: segunda pasada con umbral más suave bajo la nariz
        osc2 = (L < 58) & cara_llena & (np.arange(rgb.shape[0])[:, None] > ye + 1.2 * p['h']) & (np.abs(np.arange(rgb.shape[1])[None, :] - xc) < 0.2 * W)
        et2, n2 = ndimage.label(osc2)
        for i in range(1, n2 + 1):
            m = et2 == i; A = m.sum()
            if A < 0.0002 * W * H: continue
            cx0, cy0, cx1, cy1 = caja(m); comps.append({'cx': (cx0 + cx1) / 2, 'cy': (cy0 + cy1) / 2, 'w': cx1 - cx0 + 1, 'h': cy1 - cy0 + 1, 'area': int(A)})
        bocas = [c for c in comps if c['cy'] > ye + 1.2 * p['h'] and c['cy'] < y1 - 0.03 * H and abs(c['cx'] - xc) < 0.15 * W and c['w'] > c['h']]
        if bocas:
            bo = max(bocas, key=lambda c: c['area']); out['boca'] = {'y_bajo_ojo': rel(bo['cy'] - ye), 'ancho': rel(bo['w']), 'alto': rel(bo['h'])}
        # nariz: piel con sombra (L más bajo que la mediana de la cara) en la franja central entre ojos y boca
        Lc = np.median(L[cara]); franja = cara & (np.abs(np.arange(rgb.shape[1])[None, :] - xc) < 0.12 * W)
        franja &= (np.arange(rgb.shape[0])[:, None] > ye) & (np.arange(rgb.shape[0])[:, None] < ye + 0.35 * H)
        sombra = franja & (L < Lc - 6)
        if sombra.sum() > 0.0005 * W * H:
            sm = mayor(sombra); sx0, sy0, sx1, sy1 = caja(sm)
            out['nariz'] = {'y_bajo_ojo': rel((sy0 + sy1) / 2 - ye), 'ancho': rel(sx1 - sx0 + 1), 'alto': rel(sy1 - sy0 + 1)}
    out['alto_sobre_ancho_cara'] = H / W
    # altura total de la figura (todo lo que no es fondo, mancha mayor) para escalar la cabeza al cuerpo
    fondo = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), 0)
    fig = mayor(np.linalg.norm(rgb - fondo, axis=-1) > 40); fy = np.where(fig.any(1))[0]
    out['ancho_cara_sobre_altura'] = round(W / (fy[-1] - fy[0]), 4); out['barbilla_sobre_altura'] = round((fy[-1] - y1) / (fy[-1] - fy[0]), 4)
    out['comps_oscuros'] = len(comps)
    return out

if __name__ == '__main__':
    args = sys.argv[1:]; src, dst = args[0], args[1]
    rec = None; vista = 'frente'; dbg = None
    if '--recorte' in args: rec = [int(v) for v in args[args.index('--recorte') + 1].split(',')]
    if '--vista' in args: vista = args[args.index('--vista') + 1]
    if '--debug' in args: dbg = args[args.index('--debug') + 1]
    im = Image.open(src).convert('RGB')
    if rec: im = im.crop(rec)
    rgb = np.asarray(im, dtype=np.float64)
    out = medir(rgb, vista); out['fuente'] = src; out['recorte'] = rec
    json.dump(out, open(dst, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k not in ('px',)}, ensure_ascii=False, indent=1))
    if dbg:
        from PIL import ImageDraw
        d = ImageDraw.Draw(im); x0, y0, x1, y1 = out['px']['cara']; d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=3)
        W = out['px']['ancho_cara']
        if 'ojos' in out:
            o = out['ojos']; cx = (x0 + x1) / 2; ye = y0 + o['y_desde_arriba'] * W
            for s in (-1, 1):
                ex = cx + s * o['separacion'] * W / 2; d.ellipse([ex - o['ancho'] * W / 2, ye - o['alto'] * W / 2, ex + o['ancho'] * W / 2, ye + o['alto'] * W / 2], outline=(0, 200, 0), width=3)
            if 'boca' in out: b = out['boca']; yb = ye + b['y_bajo_ojo'] * W; d.rectangle([cx - b['ancho'] * W / 2, yb - b['alto'] * W / 2, cx + b['ancho'] * W / 2, yb + b['alto'] * W / 2], outline=(0, 0, 255), width=3)
            if 'nariz' in out: nz = out['nariz']; yn = ye + nz['y_bajo_ojo'] * W; d.rectangle([cx - nz['ancho'] * W / 2, yn - nz['alto'] * W / 2, cx + nz['ancho'] * W / 2, yn + nz['alto'] * W / 2], outline=(255, 140, 0), width=3)
        im.save(dbg)
