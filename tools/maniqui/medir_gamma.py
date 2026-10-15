"""Mide la cara de Gamma (malla 3D texturizada) sobre renders ortográficos sin sombreado + mapa de profundidad.
Frente: ojos (esclerótica blanca + iris café, que los lentes de Gamma no tapan: son sólo aros), cejas, nariz, boca, ancho de cara.
Lado: cuánto sale la nariz, hundimiento de los ojos, posición y tamaño de la oreja.
Escribe rasgos en fracciones del ancho de cara W (formato de cabeza.py) + W en metros.
Uso: medir_gamma.py gamma.glb salida.json [--debug out.png]     (numpy + scipy + Pillow, sin IA)"""
import json, sys
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
import render
from medir_cara import srgb_a_lab, mayor, caja

src, dst = sys.argv[1], sys.argv[2]
dbg = sys.argv[sys.argv.index('--debug') + 1] if '--debug' in sys.argv else None
tris = render.gather(src)
allv = np.concatenate([t[0].reshape(-1, 3) for t in tris]); Ht = allv[:, 1].max() - allv[:, 1].min(); ybase = allv[:, 1].min()
R = 0.32 * Ht                                                     # caja de la cabeza
B = (np.array([-R, ybase + 0.48 * Ht, -R]), np.array([R, ybase + 0.48 * Ht + 2 * R, R]))
PX = 1000
ctr = (B[0] + B[1]) / 2
def vista(yaw):
    img, zb, sc = render.render(tris, yaw, W=PX, H=PX, bounds=B, unlit=True, depth=True)
    return np.asarray(img, dtype=np.float64), zb, sc
img, zb, sc = vista(0)
lab = srgb_a_lab(img); L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]; cro = np.hypot(a, b)
yy, xx = np.mgrid[0:PX, 0:PX]
mx = lambda px: (px - PX / 2) / sc + ctr[0]                       # px → metros
my = lambda py: -(py - PX / 2) / sc + ctr[1]
piel = (L > 50) & (a > 8) & (b > 8) & (a >= 0.36 * b) & np.isfinite(zb)
piel = ndimage.binary_opening(piel, iterations=2)
# cara = mancha de piel mayor tras cerrar los aros de los lentes y cejas
r = 18; dil = ndimage.distance_transform_edt(~piel) <= r
cara = ndimage.binary_fill_holes(mayor(ndimage.distance_transform_edt(dil) > r))
x0, y0, x1, y1 = caja(cara)
xc = int(np.median(np.where(cara[(y0 + y1) // 2])[0]))
def corrida(fila_mask, x):
    """ancho de la corrida de True que contiene x (sin brincar huecos: separa la oreja de la cara)"""
    if not fila_mask[x]: return 0
    izq = x - np.argmax(~fila_mask[x::-1]) if (~fila_mask[x::-1]).any() else 0
    der = x + np.argmax(~fila_mask[x:]) if (~fila_mask[x:]).any() else len(fila_mask)
    return der - izq
piel_c = ndimage.binary_closing(piel, iterations=4)               # cierra poros, no une la oreja (hay pelo entre medio)
anch = np.array([corrida(piel_c[y] | (cara[y] & ~piel[y] & (np.abs(np.arange(PX) - xc) < 0.3 * (x1 - x0))), xc) for y in range(PX)])
tip = np.percentile(anch[y0:y1 + 1][anch[y0:y1 + 1] > 0], 70)
abajo = np.where(anch[::-1][PX - 1 - y1:] >= 0.6 * tip)[0]     # de abajo hacia arriba: primera fila ancha = barbilla
y1 = y1 - int(abajo[0]) if len(abajo) else y1
cara[y1 + 1:] = False
Hf = y1 - y0
Wpx = int(np.percentile(anch[y0 + Hf // 4: y1 - Hf // 6], 60))
filas = np.minimum(anch, Wpx)
W = Wpx / sc
rel = lambda px: round(float(px) / Wpx, 4)
out = {'_fuente': 'Gamma (alastor_gamma_30k_2k.glb), renders ortográficos sin luz + profundidad', '_unidad': 'fracciones del ancho de cara W',
       'W_m': round(float(W), 4), 'alto_sobre_ancho_cara': rel(Hf), 'ancho_cara_sobre_altura': round(float(W / Ht), 4)}
anchos = filas[y0:y1 + 1] / Wpx
out['llenado_caja'] = round(float(np.clip(anchos, 0, 1).mean()), 4)
out['ancho_abajo'] = round(float(np.median(anchos[-max(3, Hf // 10):])), 4)
# --- ojos: el hueco de cada aro de los lentes, menos la piel (Gamma tiene aros sin cristal: el ojo se ve completo)
aro = (L < 45) & (cro < 16) & (b < 3) & (yy > y0) & (yy < y1)   # aro: negro-azulado (el iris es café: b > 5); sin recortar a la cara para que los aros cierren
aro = ndimage.binary_closing(aro, iterations=2)
huecos = ndimage.binary_fill_holes(aro) & ~aro
ojo_m = huecos & ~piel & ~aro
ojo_m = ndimage.binary_opening(ojo_m, iterations=2)
ojos = {}
for s_, lado in (('L', xx > xc + 0.04 * Wpx), ('R', xx < xc - 0.04 * Wpx)):
    m = ojo_m & lado
    if m.sum() < 50: continue
    m = ndimage.binary_fill_holes(mayor(m)); ox0, oy0, ox1, oy1 = caja(m)
    ir = ndimage.binary_opening(m & (L < 40) & (b > 2), iterations=2); ir = mayor(ir) if ir.any() else ir; ix0, iy0, ix1, iy1 = caja(ir) if ir.sum() > 20 else (ox0, oy0, ox1, oy1)
    # forma: llenado de la caja (1 = rectángulo, 0.785 = elipse) y si el borde superior es recto
    filas_o = m[oy0:oy1 + 1].sum(1); arriba = filas_o[: max(2, len(filas_o) // 6)].mean() / filas_o.max()
    ojos[s_] = dict(cx=(ox0 + ox1) / 2, cy=(oy0 + oy1) / 2, w=ox1 - ox0, h=oy1 - oy0, iw=ix1 - ix0, ih=iy1 - iy0, mask=m, iris=ir,
                    llenado=float(m[oy0:oy1 + 1, ox0:ox1 + 1].mean()), arriba=float(arriba))
if len(ojos) == 2:
    l, rr = ojos['L'], ojos['R']; ye = (l['cy'] + rr['cy']) / 2
    out['ojos'] = {'separacion': rel(abs(l['cx'] - rr['cx'])), 'ancho': rel((l['w'] + rr['w']) / 2), 'alto': rel((l['h'] + rr['h']) / 2),
                   'y_sobre_barbilla': rel(y1 - ye), 'iris_ancho': rel((l['iw'] + rr['iw']) / 2), 'iris_alto': rel((l['ih'] + rr['ih']) / 2),
                   'llenado_caja': round((l['llenado'] + rr['llenado']) / 2, 3), 'ancho_borde_superior': round((l['arriba'] + rr['arriba']) / 2, 3)}
    top = min(l['cy'] - l['h'] / 2, rr['cy'] - rr['h'] / 2)
    # cejas: café oscuro saturado arriba de los ojos, dentro de la cara
    zona = cara & (yy < top) & (yy > top - 0.30 * Wpx)
    cj = zona & (L < 45) & (cro > 10) & (L > 10)
    cj = ndimage.binary_opening(cj, iterations=1); ce = {}
    for s, xs in (('L', xx > xc + 0.03 * Wpx), ('R', xx < xc - 0.03 * Wpx)):
        m = cj & xs
        if m.sum() < 20: continue
        m = mayor(m); cx0, cy0, cx1, cy1 = caja(m); cols = np.where(m.any(0))[0]
        inner = cols.min() if s == 'L' else cols.max(); outer = cols.max() if s == 'L' else cols.min()
        yin = np.mean(np.where(m[:, inner])[0]); yout = np.mean(np.where(m[:, outer])[0])
        ce[s] = dict(cy=(cy0 + cy1) / 2, w=cx1 - cx0, h=np.median(m.sum(0)[m.sum(0) > 0]), incl=yout - yin)   # >0: interior más bajo (ceño)
    if len(ce) == 2:
        out['cejas'] = {'y_sobre_ojo': rel(ye - np.mean([c['cy'] for c in ce.values()])), 'ancho': rel(np.mean([c['w'] for c in ce.values()])),
                        'alto': rel(np.mean([c['h'] for c in ce.values()])), 'ceno': rel(np.mean([c['incl'] for c in ce.values()]))}
    # boca: línea oscura bajo la nariz (más oscura que la piel), centrada
    Lp = np.median(L[cara & piel])
    zb_c = np.where(np.isfinite(zb), zb, -9)
    bo = cara & piel_c & (yy > ye + 0.25 * Wpx) & (yy < y1 - 0.03 * Wpx) & (np.abs(xx - xc) < 0.2 * Wpx) & (L < Lp - 15) & ~aro
    bo = ndimage.binary_opening(bo, iterations=1)
    if bo.sum() > 10:
        bo = mayor(bo); bx0, by0, bx1, by1 = caja(bo)
        out['boca'] = {'y_bajo_ojo': rel((by0 + by1) / 2 - ye), 'ancho': rel(bx1 - bx0), 'alto': rel(max(by1 - by0, 2))}
    # nariz: en la profundidad, lo que sale del plano de la cara en la franja central bajo los ojos
    ref = np.full(PX, np.nan)
    for y in range(int(ye), y1):
        lado_z = [zb_c[y, int(xc + k * 0.22 * Wpx)] for k in (-1, 1)]
        ref[y] = np.mean(lado_z)
    zface = np.nanmedian(ref)
    sobre = zb_c - np.where(np.isnan(ref), np.inf, ref)[:, None]
    nz = cara & piel & ~ndimage.binary_dilation(aro, iterations=3) & (np.abs(xx - xc) < 0.12 * Wpx) & (yy > ye - 0.05 * Wpx) & (yy < ye + 0.45 * Wpx) & (sobre > 0.012)
    nz = ndimage.binary_opening(nz, iterations=2)
    if nz.sum() > 10:
        nz = mayor(nz); nx0, ny0, nx1, ny1 = caja(nz)
        out['nariz'] = {'y_bajo_ojo': rel((ny0 + ny1) / 2 - ye), 'ancho': rel(nx1 - nx0), 'alto': rel(ny1 - ny0), 'sale': round(float(sobre[nz].max() / W), 4)}
    out['_ojos_hundidos'] = round(float(np.nanmedian(sobre[l['mask'] | rr['mask']]) / W), 4)
    # orejas: piel fuera del ancho de cara a los lados
    ores = []
    for s in (1, -1):
        m = piel & ((xx - xc) * s > Wpx / 2 + 2) & (yy > ye - 0.3 * Wpx) & (yy < ye + 0.3 * Wpx)
        if m.sum() < 20: continue
        m = mayor(m); ox0, oy0, ox1, oy1 = caja(m)
        # lo que sale la oreja se mide desde la mejilla en esas mismas filas (la cara es más ancha que W a la altura de la oreja)
        filas_o = range(oy0, oy1 + 1); ext = [(np.where(m[y])[0].max() if s > 0 else np.where(m[y])[0].min()) for y in filas_o if m[y].any()]
        mej = [xc + s * anch[y] / 2 for y in filas_o if m[y].any()]
        ores.append(dict(sale=float(np.percentile([abs(e - q) for e, q in zip(ext, mej)], 90)), alto=(oy1 - oy0), cy=(oy0 + oy1) / 2))
    if ores:
        out['orejas'] = {'sale': rel(np.mean([o['sale'] for o in ores])), 'alto': rel(np.mean([o['alto'] for o in ores])), 'y_sobre_barbilla': rel(y1 - np.mean([o['cy'] for o in ores]))}
# --- lado: fondo de la oreja y su posición en z
img2, zb2, _ = vista(90)
lab2 = srgb_a_lab(img2); L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]
piel2 = ndimage.binary_opening((L2 > 50) & (a2 > 8) & (b2 > 8) & (a2 >= 0.36 * b2) & np.isfinite(zb2), iterations=2)
if 'ojos' in out:
    yeg = ye  # misma escala y encuadre vertical
    lob = piel2 & (np.abs(yy - yeg) < 0.35 * Wpx)
    et2, n2 = ndimage.label(lob); best = None
    for i in range(1, n2 + 1):     # la oreja: mancha de piel separada de la cara (la cara es la que llega más adelante)
        m = et2 == i
        if m.sum() < 30: continue
        cx0, cy0, cx1, cy1 = caja(m)
        if best is None or cx0 < best[1][0]: best = (m, (cx0, cy0, cx1, cy1))
    # en yaw 90 el frente (+Z) queda a la izquierda/derecha según el rasterizador: tomo la mancha más alejada del frente
    comps2 = [(et2 == i) for i in range(1, n2 + 1) if (et2 == i).sum() >= 30]
    if len(comps2) >= 2:
        comps2.sort(key=lambda m: np.mean(np.where(m)[1]))
        frente_izq = np.mean(np.where(comps2[0])[1]) < np.mean(np.where(comps2[-1])[1])
        cara2 = max(comps2, key=lambda m: m.sum())
        oreja2 = [m for m in comps2 if m is not cara2]
        if oreja2:
            o2 = max(oreja2, key=lambda m: m.sum()); ox0, oy0, ox1, oy1 = caja(o2); fx0, fy0, fx1, fy1 = caja(cara2)
            out.setdefault('orejas', {})['fondo'] = rel(ox1 - ox0)
            out['orejas']['alto_lado'] = rel(oy1 - oy0)
            out['orejas']['detras_de_cara'] = rel(min(abs(ox0 - fx1), abs(fx0 - ox1)))
    out['fondo_cabeza_sobre_W'] = rel(np.ptp(np.where(np.isfinite(zb2).any(0))[0]))
    # nariz de perfil: rebanada central |x - x_eje| < 2.5 cm (fuera de los aros de los lentes); punta vs línea de la cara bajo la nariz
    if 'nariz' in out and 'boca' in out:
        x_eje = mx(xc)
        reb = [(t[0][np.abs(t[0][:, :, 0].mean(1) - x_eje) < 0.025],) + t[1:] for t in tris]
        reb = [(v, c, uv[np.abs(t[0][:, :, 0].mean(1) - x_eje) < 0.025] if uv is not None else None, tx, None) for (v, c, uv, tx, _), t in zip(reb, tris) if len(v)]
        _, zb3, sc3 = render.render(reb, 90, W=PX, H=PX, bounds=B, unlit=True, depth=True)
        def borde(y):
            c = np.where(np.isfinite(zb3[int(round(y))]))[0]; return c
        yn0 = ye + (out['nariz']['y_bajo_ojo'] - out['nariz']['alto'] / 2) * Wpx; yn1 = ye + (out['nariz']['y_bajo_ojo'] + out['nariz']['alto'] / 2) * Wpx
        ym = ye + out['boca']['y_bajo_ojo'] * Wpx
        fm = borde(ym)
        puntas = [borde(y) for y in np.linspace(yn0, yn1, 12)]
        if len(fm):
            lado_frente = 1                                   # con yaw 90 el rasterizador pone +Z (frente) a la derecha
            sale = max((p.max() - fm.max()) if lado_frente > 0 else (fm.min() - p.min()) for p in puntas if len(p))
            out['nariz']['sale'] = rel(sale)
            # alto real de la nariz (de perfil): filas donde la silueta sale > 25 % de la punta
            filas_n = [y for y in range(int(ye), int(ym)) if len(borde(y)) and ((borde(y).max() - fm.max()) if lado_frente > 0 else (fm.min() - borde(y).min())) > 0.25 * sale]
            if filas_n: out['nariz']['alto'] = rel(max(filas_n) - min(filas_n)); out['nariz']['y_bajo_ojo'] = rel((max(filas_n) + min(filas_n)) / 2 - ye)
json.dump(out, open(dst, 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
if dbg:
    im = Image.fromarray(img.astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle([xc - Wpx // 2, y0, xc + Wpx // 2, y1], outline=(255, 0, 0), width=3)
    for o in ojos.values():
        d.rectangle([o['cx'] - o['w'] / 2, o['cy'] - o['h'] / 2, o['cx'] + o['w'] / 2, o['cy'] + o['h'] / 2], outline=(0, 220, 0), width=3)
    if 'nariz' in out: d.rectangle([nx0, ny0, nx1, ny1], outline=(255, 140, 0), width=3)
    if 'boca' in out: d.rectangle([bx0, by0, bx1, by1], outline=(0, 0, 255), width=3)
    im.crop((xc - Wpx, y0 - Wpx // 2, xc + Wpx, y1 + Wpx // 6)).save(dbg)
