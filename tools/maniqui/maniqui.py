"""Maniquí gris a partir de Alastor Delta + archivo de ropa por piezas.
Uso: maniqui.py delta.glb it4c.glb maniqui_out.glb ropa_out.glb"""
import json, struct, sys, io
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import render

DELTA, IT4C, OUT_M, OUT_R = sys.argv[1:5]
GRIS = [0.42, 0.42, 0.44, 1.0]

def load_prims(path):
    j, b = render.load(path); mesh = j['meshes'][0]; out = []
    for p in mesh['primitives']:
        A = p['attributes']; I = render.acc(j, b, p['indices']).astype(int).reshape(-1, 3)
        if len(I) == 0: continue
        d = dict(name=j['materials'][p['material']]['name'], P=render.acc(j, b, A['POSITION']), N=render.acc(j, b, A['NORMAL']),
                 J=render.acc(j, b, A['JOINTS_0']).astype(int), W=render.acc(j, b, A['WEIGHTS_0']), I=I,
                 UV=render.acc(j, b, A['TEXCOORD_0']) if 'TEXCOORD_0' in A else None, mat=j['materials'][p['material']])
        out.append(d)
    return j, b, out

jd, bd, dprims = load_prims(DELTA)
_, _, cprims = load_prims(IT4C)
def compact(P, N, J, W, I, UV=None):
    used = np.unique(I); remap = -np.ones(len(P), int); remap[used] = np.arange(len(used))
    return dict(P=P[used], N=N[used], J=J[used], W=W[used], I=remap[I], UV=None if UV is None else UV[used])
def sub(d, tri_mask): return compact(d['P'], d['N'], d['J'], d['W'], d['I'][tri_mask], d['UV'])

# ---------- cabeza: separar piel / pelo / lentes por color de textura
head = [d for d in dprims if d['name'] == 'GammaHead'][0]
himg = jd['images'][jd['textures'][head['mat']['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
hbv = jd['bufferViews'][himg['bufferView']]; ho = hbv.get('byteOffset', 0)
TEX = np.asarray(Image.open(io.BytesIO(bd[ho:ho + hbv['byteLength']])).convert('RGB'), dtype=np.float64)
th, tw = TEX.shape[:2]
I0 = head['I']; UVc = head['UV'][I0].mean(1)                                 # color por centro de triángulo (dentro de la isla UV)
C = TEX[(np.mod(UVc[:, 1], 1) * (th - 1)).astype(int), (np.mod(UVc[:, 0], 1) * (tw - 1)).astype(int)]
lum = C.mean(1); chroma = (C + 1) / (C + 1).sum(1, keepdims=True)
yc = head['P'][I0, 1].mean(1); y = head['P'][:, 1]; H = y.max() - y.min()
cen = head['P'][I0].mean(1)
back = (cen[:, 2] - np.median(head['P'][:, 2])) * (np.sign(np.median(head['P'][I0, 2].mean(1)) - np.median(head['P'][:, 2])) or 1) < 0
tri_hair = ((chroma[:, 0] > 0.44) & (chroma[:, 2] < 0.22) & (lum < 112) & (yc > y.min() + 0.30 * H)) | \
           ((chroma[:, 0] > 0.42) & (chroma[:, 2] < 0.25) & (lum < 140) & back & (yc > y.min() + 0.20 * H))
tri_glass = (lum < 95) & (chroma[:, 0] < 0.42) & ~tri_hair & (yc > y.min() + 0.26 * H) & (yc < y.min() + 0.55 * H)
# lentes por plantilla: los lentes de Beta (misma posición) marcan qué triángulos de Gamma son lente
import struct as _st
bj, bb, bprims = load_prims(sys.argv[5]) if len(sys.argv) > 5 else (None, None, [])
G = [d for d in bprims if d['name'] == 'Glasses']
cen = head['P'][I0].mean(1)
if G:
    GP_ = G[0]['P']; d = np.empty(len(cen))
    for i in range(0, len(cen), 1500): d[i:i + 1500] = np.sqrt(((cen[i:i + 1500, None] - GP_[None]) ** 2).sum(-1).min(1))
    eyes = (lum > 185) & (yc > y.min() + 0.33 * H) & (yc < y.min() + 0.50 * H)
    eye_c = [cen[eyes & (cen[:, 0] < np.median(cen[:, 0]))].mean(0), cen[eyes & (cen[:, 0] >= np.median(cen[:, 0]))].mean(0)]
    near_eye = np.min([np.linalg.norm(cen - c, axis=1) for c in eye_c], axis=0) < 0.021
    geo = (d < 0.014) & ~tri_hair & ~near_eye
    tri_glass |= geo; print('lentes por plantilla de Beta:', geo.sum(), '| ojos protegidos:', near_eye.sum())
tri_skin = ~tri_hair & ~tri_glass
print(f'cabeza: piel {tri_skin.sum()} tris, pelo {tri_hair.sum()}, lentes {tri_glass.sum()}')
# segunda pasada: la bola del cráneo (ancho de la cara, centro bajo los ojos) decide qué 'pelo' es en realidad piel en sombra
_sk = head['P'][np.unique(head['I'][tri_skin])]
_cx = (_sk[:, 0].min() + _sk[:, 0].max()) / 2; _rx = np.percentile(np.abs(_sk[:, 0] - _cx), 99.5)
_hp = head['P'][np.unique(head['I'][tri_hair])]
_ctr = np.array([_cx, float(np.mean([c[1] for c in eye_c])) - 0.03, (_sk[:, 2].max() + _hp[:, 2].min()) / 2])
_rad = np.array([_rx, _rx * 1.04, (_sk[:, 2].max() - _hp[:, 2].min()) / 2 * 0.98])
_d = cen - _ctr; _rr = np.sqrt(((_d / _rad) ** 2).sum(1))                      # 1.0 = sobre la esfera
on_ball = (_rr < 0.985) & (cen[:, 1] < _ctr[1] + 0.09)                           # sobre/dentro de la bola y por debajo de la coronilla
tri_hair &= ~on_ball; tri_skin = ~tri_hair & ~tri_glass
print('pelo devuelto a piel por estar sobre la esfera:', int(on_ball.sum()))
pelo = sub(head, tri_hair); lentes = sub(head, tri_glass); cara = sub(head, tri_skin)

# ---------- cráneo = superficie interior de la cáscara de pelo (mínimo radial por dirección), suavizada
skin_pts = cara['P']; hp = pelo['P']
ctr = np.array([(skin_pts[:, 0].min() + skin_pts[:, 0].max()) / 2, np.percentile(skin_pts[:, 1], 55), (hp[:, 2].min() + hp[:, 2].max()) / 2])
NT, NP = 48, 24
def sph(Pq):
    d = Pq - ctr; r = np.linalg.norm(d, axis=1); th = np.arctan2(d[:, 2], d[:, 0]); ph = np.arccos(np.clip(d[:, 1] / (r + 1e-9), -1, 1))
    return r, th, ph
r, th, ph = sph(hp); it = ((th + np.pi) / (2 * np.pi) * NT).astype(int) % NT; ip = np.clip((ph / np.pi * NP).astype(int), 0, NP - 1)
R = np.full((NP, NT), np.nan)
for k in range(len(hp)):
    if np.isnan(R[ip[k], it[k]]) or r[k] < R[ip[k], it[k]]: R[ip[k], it[k]] = r[k]
# bins con cara: la cara manda ahí (no hay cúpula)
rs, ths, phs = sph(skin_pts); its = ((ths + np.pi) / (2 * np.pi) * NT).astype(int) % NT; ips = np.clip((phs / np.pi * NP).astype(int), 0, NP - 1)
Rf = np.zeros((NP, NT)); Cf = np.zeros((NP, NT), int)
for k in range(len(rs)): Rf[ips[k], its[k]] = max(Rf[ips[k], its[k]], rs[k]); Cf[ips[k], its[k]] += 1
face_bin = Cf >= 2
hair_bin = ~np.isnan(R)
# cabeza redonda: ancho desde la cara (sin orejas), fondo desde el volumen de la cabeza, alto = ancho
y_eye0 = float(np.mean([c[1] for c in eye_c]))
rx = np.percentile(np.abs(skin_pts[:, 0] - ctr[0]), 99.5)
rz = (skin_pts[:, 2].max() - hp[:, 2].min()) / 2 * 0.98
ry = rx * 1.04
ctr = np.array([ctr[0], y_eye0 - 0.03, (skin_pts[:, 2].max() + hp[:, 2].min()) / 2])
print(f'cráneo esférico: rx {rx*100:.1f} ry {ry*100:.1f} rz {rz*100:.1f} cm')
RE = np.zeros((NP, NT))
for i in range(NP):
    for k in range(NT):
        t_ = (k + 0.5) / NT * 2 * np.pi - np.pi; p_ = (i + 0.5) / NP * np.pi
        n = np.array([np.sin(p_) * np.cos(t_), np.cos(p_), np.sin(p_) * np.sin(t_)])
        RE[i, k] = 1 / np.sqrt((n ** 2 / np.array([rx, ry, rz]) ** 2).sum())
R = RE
upper = np.arange(NP)[:, None] < int(NP * 0.85)
nof = ~face_bin
edge = np.zeros_like(nof)
for i in range(NP):
    for k in range(NT):
        if face_bin[i, k] and any(nof[i2, k2 % NT] for i2 in (i - 1, i, i + 1) for k2 in (k - 1, k, k + 1) if 0 <= i2 < NP): edge[i, k] = True
valid = np.broadcast_to(upper, (NP, NT)).copy()
y_brow = float(np.mean([c[1] for c in eye_c])) + 0.045
for i in range(NP):
    for k in range(NT):
        if not valid[i, k]: continue
        t_ = (k + 0.5) / NT * 2 * np.pi - np.pi; p_ = (i + 0.5) / NP * np.pi
        pos = ctr + R[i, k] * np.array([np.sin(p_) * np.cos(t_), np.cos(p_), np.sin(p_) * np.sin(t_)])
        fr = (pos[2] - ctr[2]) * float(np.sign(np.mean([c[2] for c in eye_c]) - ctr[2]) or 1.0)
        face_zone = fr > 0.10 and abs(pos[0] - ctr[0]) < 0.70 * rx       # delante y dentro del ancho de la cara
        if face_zone and pos[1] < y_brow: valid[i, k] = False               # frente: respeta la cara desde la ceja
        ear_zone = abs(pos[0] - ctr[0]) > 0.80 * rx and abs(pos[2] - ctr[2]) < 0.45 * rz and pos[1] < y_brow - 0.035
        if (not face_zone) and (pos[1] < y_brow - 0.12 or ear_zone): valid[i, k] = False  # costados: hasta la oreja, sin taparla
# la cara que queda fuera de la bola en la zona cubierta se recorta
_d = cara['P'] - ctr; _rr = np.sqrt(((_d / np.array([rx, ry, rz])) ** 2).sum(1))
_fr = (cara['P'][:, 2] - ctr[2]) * float(np.sign(np.mean([c[2] for c in eye_c]) - ctr[2]) or 1.0)
_fz = (_fr > 0.10) & (np.abs(cara['P'][:, 0] - ctr[0]) < 0.70 * rx)
_ez = (np.abs(cara['P'][:, 0] - ctr[0]) > 0.80 * rx) & (np.abs(cara['P'][:, 2] - ctr[2]) < 0.45 * rz) & (cara['P'][:, 1] < y_brow - 0.035)
cut_out = (_rr > 0.97) & (cara['P'][:, 1] > y_brow - 0.12) & (~_fz | (cara['P'][:, 1] > y_brow)) & ~_ez
cut_in = (_rr < 0.96) & (cara['P'][:, 1] > y_brow - 0.12) & (~_fz | (cara['P'][:, 1] > y_brow)) & ~_ez   # restos ocultos dentro de la bola
cut_v = cut_out
keep_tri = ~cut_v[cara['I']].any(1)
cara = compact(cara['P'], cara['N'], cara['J'], cara['W'], cara['I'][keep_tri])
print('cara: triángulos recortados por quedar fuera de la bola:', int((~keep_tri).sum()), '| y_brow', round(y_brow,3), 'ctr', ctr.round(3), 'ry', round(ry,3), 'bola baja hasta y=', round(ctr[1]-ry,3))
y_eye = float(np.mean([c[1] for c in eye_c])); front_sign = float(np.sign(np.mean([c[2] for c in eye_c]) - ctr[2]) or 1.0)
P, idx = [], -np.ones((NP + 1, NT), int)
P.append(ctr + [0, np.nanmean(R[0]), 0]); top = 0
for i in range(NP):
    for k in range(NT):
        if valid[i, k]:
            t_ = (k + 0.5) / NT * 2 * np.pi - np.pi; p_ = (i + 0.5) / NP * np.pi
            idx[i + 1, k] = len(P); P.append(ctr + R[i, k] * np.array([np.sin(p_) * np.cos(t_), np.cos(p_), np.sin(p_) * np.sin(t_)]))
P = np.array(P); I = []
for k in range(NT):
    a_, b_ = idx[1, k], idx[1, (k + 1) % NT]
    if a_ >= 0 and b_ >= 0: I.append([top, b_, a_])
for i in range(1, NP):
    for k in range(NT):
        a_, b_, c_, d_ = idx[i, k], idx[i, (k + 1) % NT], idx[i + 1, k], idx[i + 1, (k + 1) % NT]
        if min(a_, b_, c_, d_) >= 0: I += [[a_, b_, c_], [b_, d_, c_]]
        elif min(a_, b_, c_) >= 0: I.append([a_, b_, c_])
        elif min(b_, d_, c_) >= 0: I.append([b_, d_, c_])
I = np.array(I)
fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); Nn = np.zeros_like(P)
for k in range(3): np.add.at(Nn, I[:, k], fn)
Nn /= (np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-12)
head_joint = int(cara['J'][0, 0])
cup = compact(P, Nn, np.tile([head_joint, 0, 0, 0], (len(P), 1)), np.tile([1, 0, 0, 0], (len(P), 1)), I)
print(f'cráneo: {len(I)} tris desde la cara interior del pelo; bins válidos {valid.sum()} de {NP*NT}')

# ---------- piezas del maniquí (de Delta y de it4c) y de la ropa
by = lambda prims, n: [d for d in prims if d['name'] == n]
belt_y = by(dprims, 'Belt')[0]['P'][:, 1].mean()
torso = [sub(d, d['P'][d['I'], 1].min(1) > belt_y - 0.01) for d in by(dprims, 'Coat')]        # gabardina sobre el cinturón = torso
piernas = by(cprims, 'Trousers'); pies = by(cprims, 'Shoes') + by(cprims, 'Sole')
brazos = by(dprims, 'Skin'); cuello = [d for d in dprims if d['name'] == 'NeckSkin']
maniqui = [('Cabeza', cara), ('Craneo', cup)] + [('Cuello', d) for d in cuello] + [('Brazos', d) for d in brazos] + \
          [('Torso', d) for d in torso] + [('Piernas', d) for d in piernas] + [('Pies', d) for d in pies]
ropa = [('Pelo', pelo), ('Lentes', lentes)] + [(n, d) for n in ('Coat', 'CoatDark', 'Shirt', 'Tie', 'Belt', 'Buckle') for d in by(cprims, n)] + \
       [('Faldones+Pantalon', [d for d in dprims if d['name'] == 'GammaHead'][1]), ('Zapatos', [d for d in dprims if d['name'] == 'GammaHead'][2])]

# ---------- escritura: mismo esqueleto/nodos/animaciones de Delta, mallas nuevas
def write(prims_named, out, textured_names=()):
    j = json.loads(json.dumps(jd)); binc = bytearray(bd[:])
    # conservar solo accessors/bufferViews de nodos/skins/animaciones: más simple, mantener todo y añadir al final
    def append_bv(data, target=None):
        while len(binc) % 4: binc.append(0)
        d = {'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data)}
        if target: d['target'] = target
        j['bufferViews'].append(d); binc.extend(data); return len(j['bufferViews']) - 1
    def add_acc(bvi, ct, n, at, arr=None):
        a = {'bufferView': bvi, 'componentType': ct, 'count': int(n), 'type': at}
        if arr is not None and at == 'VEC3': a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        j['accessors'].append(a); return len(j['accessors']) - 1
    gamma_mat = [i for i, m in enumerate(j['materials']) if m['name'] == 'GammaHead'][0]
    j['materials'].append({'name': 'Maniqui', 'pbrMetallicRoughness': {'baseColorFactor': GRIS, 'metallicFactor': 0, 'roughnessFactor': 0.9}})
    gris = len(j['materials']) - 1
    newp = []
    for name, d in prims_named:
        attrs = {}
        for key, arr, ct, at in [('POSITION', d['P'].astype(np.float32), 5126, 'VEC3'), ('NORMAL', d['N'].astype(np.float32), 5126, 'VEC3'),
                                 ('JOINTS_0', d['J'].astype(np.uint16), 5123, 'VEC4'), ('WEIGHTS_0', d['W'].astype(np.float32), 5126, 'VEC4')]:
            attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
        tex = name in textured_names and d['UV'] is not None
        if tex: attrs['TEXCOORD_0'] = add_acc(append_bv(d['UV'].astype(np.float32).tobytes(), 34962), 5126, len(d['UV']), 'VEC2')
        ii = d['I'].astype(np.uint32).ravel()
        mat = gamma_mat if tex else (gris if out == OUT_M else next((i for i, m in enumerate(j['materials']) if m['name'] == name), gris))
        newp.append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': mat, 'extras': {'pieza': name}})
    j['meshes'][0]['primitives'] = newp
    j['buffers'] = [{'byteLength': len(binc)}]
    while len(binc) % 4: binc.append(0)
    js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    with open(out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
    print('escrito', out, [n for n, _ in prims_named], round((28 + len(js) + len(binc)) / 1e6, 2), 'MB')
write(maniqui, OUT_M)
write(ropa, OUT_R, textured_names=('Pelo', 'Lentes', 'Faldones+Pantalon', 'Zapatos'))
