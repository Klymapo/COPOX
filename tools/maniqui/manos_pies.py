"""Manos con dedos y pies generados sobre los huesos del maniquí. Uso: manos_pies.py in.glb out.glb"""
import json, struct, sys
import numpy as np
sys.path.insert(0, '.')
import render
exec(open('cuerpo.py').read().split('# ---------- TORSO')[0].replace("SRC, OUT = sys.argv[1], sys.argv[2]", "SRC, OUT = sys.argv[1], sys.argv[2]"))  # reutiliza carga, loft, wj

def tube(points, radii, weights, seg=16, cap_top=True, cap_bot=False):
    """tubo a lo largo de una polilínea; anillos perpendiculares a la dirección local"""
    rings = []
    for k, (c, r) in enumerate(zip(points, radii)):
        d = (points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)]); d /= np.linalg.norm(d) + 1e-9
        up = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
        ex = np.cross(up, d); ex /= np.linalg.norm(ex); ez = np.cross(d, ex)
        rings.append((np.array(c), r, r, ex, ez))
    return loft(rings, weights, seg=seg, cap_top=cap_top, cap_bot=cap_bot)

pieces = []
for side, sgn in (('Left', 1), ('Right', -1)):
    P = lambda n: jp[side + n]
    # ----- antebrazo: del puño de la manga (donde termina BrazoX) a la muñeca
    wrist = P('Hand'); cuff = np.array([sgn * (cuff_x + 0.012), wrist[1], wrist[2]])
    pieces.append(('Antebrazo' + side[0], tube([cuff, cuff + (wrist - cuff) * 0.5, wrist], [0.036, 0.034, 0.030],
                   [wj((side + 'LowerArm', 1)), wj((side + 'LowerArm', 0.7), (side + 'Hand', 0.3)), wj((side + 'Hand', 1))], seg=24, cap_top=False, cap_bot=False)))
    # ----- palma: de la muñeca a los nudillos, aplanada (grosor en y, ancho en z)
    fingers = ['Index', 'Middle', 'Ring', 'Little']
    kn = np.array([P(f + 'Proximal') for f in fingers]); zc = kn[:, 2].mean(); zw = (kn[:, 2].max() - kn[:, 2].min()) / 2 + 0.012
    xs = [wrist[0], wrist[0] + sgn * 0.02, kn[:, 0].mean() - sgn * 0.012, kn[:, 0].mean() + sgn * 0.004]
    EY, EZ = np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    rings = [(np.array([x, wrist[1], zc * f + wrist[2] * (1 - f)]), ry, rz, EY, EZ) for x, ry, rz, f in
             [(xs[0], 0.024, 0.030, 0.0), (xs[1], 0.023, 0.036, 0.5), (xs[2], 0.021, zw, 1.0), (xs[3], 0.020, zw, 1.0)]]
    pieces.append(('Palma' + side[0], loft(rings, [wj((side + 'Hand', 1))] * 4, seg=24)))
    # ----- dedos: tubo por las falanges, con punta extrapolada
    for f, r in [('Index', 0.0100), ('Middle', 0.0100), ('Ring', 0.0095), ('Little', 0.0088)]:
        p0, p1, p2 = P(f + 'Proximal'), P(f + 'Intermediate'), P(f + 'Distal'); tip = p2 + (p2 - p1) * 0.9
        base = p0 - (p1 - p0) * 0.35
        pieces.append(('Dedo' + f + side[0], tube([base, p0, p1, p2, tip], [r, r, r * 0.97, r * 0.95, r * 0.8],
                       [wj((side + 'Hand', 1)), wj((side + f + 'Proximal', 1)), wj((side + f + 'Intermediate', 1)), wj((side + f + 'Distal', 1)), wj((side + f + 'Distal', 1))], seg=12)))
    m, p1, p2 = P('ThumbMetacarpal'), P('ThumbProximal'), P('ThumbDistal'); tip = p2 + (p2 - p1) * 0.8
    pieces.append(('DedoThumb' + side[0], tube([wrist + (m - wrist) * 0.3, m, p1, p2, tip], [0.011, 0.010, 0.0095, 0.009, 0.006],
                   [wj((side + 'Hand', 1)), wj((side + 'ThumbMetacarpal', 1)), wj((side + 'ThumbProximal', 1)), wj((side + 'ThumbDistal', 1)), wj((side + 'ThumbDistal', 1))], seg=12)))
    # ----- pie: anillos en el plano x-y a lo largo de z (talón → punta), base plana en y=0
    ank, toe = P('Foot'), P('Toes'); EX = np.array([1.0, 0, 0])
    prof = [(ank[2] - 0.060, 0.034, 0.042, 0.034, wj((side + 'Foot', 1))),          # botas ALTH: bloque ancho, techo plano, punta cuadrada
            (ank[2] - 0.040, 0.044, 0.058, 0.044, wj((side + 'Foot', 1))),
            (ank[2] + 0.010, 0.046, 0.062, 0.046, wj((side + 'Foot', 1))),
            (ank[2] + 0.050, 0.046, 0.062, 0.046, wj((side + 'Foot', 0.6), (side + 'Toes', 0.4))),
            (toe[2] + 0.020, 0.044, 0.058, 0.044, wj((side + 'Toes', 1))),
            (toe[2] + 0.055, 0.040, 0.050, 0.040, wj((side + 'Toes', 1))),
            (toe[2] + 0.070, 0.030, 0.038, 0.030, wj((side + 'Toes', 1)))]
    rings = [(np.array([ank[0], cy, z]), rx, ry, EX, EY, 3.6) for z, cy, rx, ry, _ in prof]
    pieces.append(('Pie' + side[0], loft(rings, [w for *_, w in prof], seg=24)))

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
