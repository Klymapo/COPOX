"""Manos con dedos y pies generados sobre los huesos del maniquí. Uso: manos_pies.py in.glb out.glb"""
import json, struct, sys
import numpy as np
sys.path.insert(0, '.')
import render
exec(open('cuerpo.py').read().split('# ---------- TORSO')[0].replace("SRC, OUT = sys.argv[1], sys.argv[2]", "SRC, OUT = sys.argv[1], sys.argv[2]"))  # reutiliza carga, loft, wj

def tube(points, radii, weights, seg=16, cap_top=True, cap_bot=False, p=None):
    """tubo a lo largo de una polilínea; anillos perpendiculares a la dirección local"""
    rings = []
    for k, (c, r) in enumerate(zip(points, radii)):
        d = (points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)]); d /= np.linalg.norm(d) + 1e-9
        up = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
        ex = np.cross(up, d); ex /= np.linalg.norm(ex); ez = np.cross(d, ex)
        rings.append((np.array(c), r, r, ex, ez))
    return loft(rings, weights, seg=seg, cap_top=cap_top, cap_bot=cap_bot, p=p)

pieces = []
for side, sgn in (('Left', 1), ('Right', -1)):
    P = lambda n: jp[side + n]
    # ----- antebrazo: del puño de la manga (donde termina BrazoX) a la muñeca
    wrist = P('Hand'); cuff = np.array([sgn * (cuff_x + 0.012), wrist[1], wrist[2]])
    # anillos elípticos: del puño (r 3.4) a la muñeca (2.1 de grueso × 2.7 de ancho ≈ 0.75 del ancho de palma, como la referencia)
    EYa, EZa = np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    fa = [(cuff, 0.034, 0.034, wj((side + 'LowerArm', 1))), (cuff + (wrist - cuff) * 0.5, 0.027, 0.030, wj((side + 'LowerArm', 0.7), (side + 'Hand', 0.3))),
          (wrist - (wrist - cuff) * 0.08, 0.021, 0.027, wj((side + 'Hand', 1))), (wrist + (wrist - cuff) * 0.12, 0.020, 0.028, wj((side + 'Hand', 1)))]
    pieces.append(('Antebrazo' + side[0], loft([(np.array(c), ry, rz, EYa, EZa) for c, ry, rz, _ in fa], [w for *_, w in fa], seg=24, cap_top=False, cap_bot=False)))
    # ----- palma: de la muñeca a los nudillos, aplanada (grosor en y, ancho en z)
    fingers = ['Index', 'Middle', 'Ring', 'Little']
    kn = np.array([P(f + 'Proximal') for f in fingers]); zc = kn[:, 2].mean(); zw = (kn[:, 2].max() - kn[:, 2].min()) / 2 + 0.012
    xs = [wrist[0], wrist[0] + sgn * 0.02, kn[:, 0].mean() - sgn * 0.012, kn[:, 0].mean() + sgn * 0.004]
    EY, EZ = np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    # palma redondeada: 7 anillos, contorno que se abre y se cierra en curva (no trapecio), sección más ovalada (exponente 2.3)
    x0p, x1p = xs[0], kn[:, 0].mean() + sgn * 0.006; zf = zw + 0.004
    perfil = []
    for k_ in range(7):
        u = k_ / 6; x = x0p + (x1p - x0p) * u
        rz = 0.030 + (zf - 0.030) * np.sin(min(u * 1.15, 1) * np.pi / 2) - 0.010 * max(u - 0.85, 0) / 0.15   # ancho: curva suave, redondeo al final
        ry = 0.019 - 0.004 * u - 0.004 * max(u - 0.85, 0) / 0.15                                             # grosor: baja hacia los nudillos
        perfil.append((x, ry, rz, min(u * 2, 1.0)))
    rings = [(np.array([x, wrist[1], zc * f + wrist[2] * (1 - f)]), ry, rz, EY, EZ, 2.3) for x, ry, rz, f in perfil]
    pieces.append(('Palma' + side[0], loft(rings, [wj((side + 'Hand', 1))] * len(rings), seg=24)))
    # ----- dedos: tubo por las falanges, con punta extrapolada
    for f, r in [('Index', 0.0110), ('Middle', 0.0112), ('Ring', 0.0107), ('Little', 0.0095)]:
        p0, p1, p2 = P(f + 'Proximal'), P(f + 'Intermediate'), P(f + 'Distal'); tip = p2 + (p2 - p1) * 0.8           # largo completo (ref: mano-con-regla-vistas.jpg)
        base = p0 - (p1 - p0) * 0.35
        pieces.append(('Dedo' + f + side[0], tube([base, p0, p1, p2, tip], [r, r, r * 0.97, r * 0.94, r * 0.88],
                       [wj((side + 'Hand', 1)), wj((side + f + 'Proximal', 1)), wj((side + f + 'Intermediate', 1)), wj((side + f + 'Distal', 1)), wj((side + f + 'Distal', 1))], seg=12, p=3.2, cap_top=True)))
    m, p1, p2 = P('ThumbMetacarpal'), P('ThumbProximal'), P('ThumbDistal'); tip = p2 + (p2 - p1) * 0.8
    # base del pulgar (eminencia tenar): volumen que nace dentro de la palma y se funde con el pulgar; tapa el canal entre pulgar e índice
    # relleno entre el pulgar y el borde de la palma: tubo que corre a medio camino entre el eje del pulgar y el interior de la palma
    pts_p = [wrist + (m - wrist) * 0.25, m, m + (p1 - m) * 0.5, p1]
    def hacia_palma(q, f): return q + (np.array([q[0], wrist[1], zc]) - q) * f
    ruta = [hacia_palma(q, f) for q, f in zip(pts_p, (0.55, 0.5, 0.4, 0.15))]
    pieces.append(('BasePulgar' + side[0], tube(ruta, [0.021, 0.021, 0.017, 0.0125],
                   [wj((side + 'Hand', 1)), wj((side + 'Hand', 0.5), (side + 'ThumbMetacarpal', 0.5)), wj((side + 'ThumbMetacarpal', 0.6), (side + 'ThumbProximal', 0.4)),
                    wj((side + 'ThumbProximal', 1))], seg=16, cap_top=True, cap_bot=True, p=2.4)))
    pieces.append(('DedoThumb' + side[0], tube([wrist + (m - wrist) * 0.3, m, p1, p2, tip], [0.0125, 0.0120, 0.0115, 0.0110, 0.0098],
                   [wj((side + 'Hand', 1)), wj((side + 'ThumbMetacarpal', 1)), wj((side + 'ThumbProximal', 1)), wj((side + 'ThumbDistal', 1)), wj((side + 'ThumbDistal', 1))], seg=12, p=3.2)))
    # ----- pie: anillos en el plano x-y a lo largo de z (talón → punta), base plana en y=0
    ank, toe = P('Foot'), P('Toes'); EX = np.array([1.0, 0, 0])
    prof = [(ank[2] - 0.068, 0.030, 0.040, 0.026, wj((side + 'Foot', 1)), 2.2),          # talón redondeado (exponente bajo atrás)
            (ank[2] - 0.060, 0.040, 0.054, 0.038, wj((side + 'Foot', 1)), 2.6),
            (ank[2] - 0.046, 0.047, 0.061, 0.047, wj((side + 'Foot', 1)), 3.2),
            (ank[2] + 0.005, 0.053, 0.065, 0.053, wj((side + 'Foot', 1)), 3.6),          # caña: abraza el tobillo
            (ank[2] + 0.040, 0.047, 0.065, 0.047, wj((side + 'Foot', 0.7), (side + 'Toes', 0.3)), 3.6),   # empeine: baja hacia la punta
            (toe[2] + 0.015, 0.039, 0.063, 0.039, wj((side + 'Toes', 1)), 3.6),
            (toe[2] + 0.050, 0.031, 0.057, 0.031, wj((side + 'Toes', 1)), 3.6),
            (toe[2] + 0.068, 0.026, 0.044, 0.020, wj((side + 'Toes', 1)), 3.2)]
    PIE = 0.8                                                                           # pies 20 % más chicos (pedido de Admin)
    prof = [(ank[2] + (z - ank[2]) * PIE, cy * PIE, max(rx * PIE, 0.047 if abs(z - ank[2]) < 0.02 else 0), ry * PIE, w, pe) for z, cy, rx, ry, w, pe in prof]
    rings = [(np.array([ank[0], cy, z]), rx, ry, EX, EY, pe) for z, cy, rx, ry, _, pe in prof]
    pieces.append(('Pie' + side[0], loft(rings, [w for _, _, _, _, w, _ in prof], seg=24)))
    # caña: collar vertical que une pierna y bota (la pierna entra en él; él entra en la bota)
    EZc = np.array([0, 0, 1.0]); cz_c = ank[2] - 0.002
    ca = [(0.030, 0.047, 0.048, wj((side + 'Foot', 1))), (0.060, 0.0455, 0.0465, wj((side + 'Foot', 0.7), (side + 'LowerLeg', 0.3))),
          (0.082, 0.0450, 0.0460, wj((side + 'LowerLeg', 0.6), (side + 'Foot', 0.4))), (0.090, 0.0445, 0.0450, wj((side + 'LowerLeg', 1)))]   # apenas más gruesa que la pierna
    rc = [(np.array([ank[0], y, cz_c]), rx, rz, EX, EZc, 2.8) for y, rx, rz, _ in ca]
    pieces.append(('Cana' + side[0], loft(rc, [w for *_, w in ca], seg=24, cap_bot=False)))
    # suela: losa un poco más ancha que la bota, 1.2 cm, punta y talón redondeados (define el pie al verlo de lado)
    sol = [(ank[2] - 0.068, 0.036), (ank[2] - 0.058, 0.056), (ank[2] - 0.045, 0.066), (ank[2] + 0.050, 0.069), (toe[2] + 0.050, 0.061), (toe[2] + 0.074, 0.040)]
    rs = [(np.array([ank[0], 0.006, ank[2] + (z - ank[2]) * PIE]), rx * PIE, 0.006, EX, EY, 5.0) for z, rx in sol]
    pieces.append(('Suela' + side[0], loft(rs, [wj((side + 'Foot', 1))] * 3 + [wj((side + 'Foot', 0.6), (side + 'Toes', 0.4))] + [wj((side + 'Toes', 1))] * 2, seg=24)))

keep = [p for p, n in zip(mesh['primitives'], names) if n not in ('Brazos', 'Pies')]
for name, (V, N, J, W, I) in pieces:
    Vl = (np.c_[V, np.ones(len(V))] @ Minv.T)[:, :3].astype(np.float32); Nl = (N @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32)
    attrs = {}
    for key, arr, ct, at in [('POSITION', Vl, 5126, 'VEC3'), ('NORMAL', Nl, 5126, 'VEC3'), ('JOINTS_0', J, 5123, 'VEC4'), ('WEIGHTS_0', W, 5126, 'VEC4')]:
        attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
    ii = I.astype(np.uint32).ravel()
    keep.append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': gris, 'extras': {'pieza': name}})
mesh['primitives'] = keep
print('piezas nuevas:', [n for n, _ in pieces])
j['buffers'] = [{'byteLength': len(binc)}]
while len(binc) % 4: binc.append(0)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
print('escrito', OUT)
