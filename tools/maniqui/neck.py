"""Pulido de cabeza + cuello nuevo (sin shrinkwrap). Uso: neck.py in.glb out.glb [y_collar] [smooth_passes]"""
import json, struct, sys
import numpy as np
sys.path.insert(0, '.')
import render

SRC, OUT = sys.argv[1], sys.argv[2]
Y_COLLAR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.48     # hasta dónde baja el cuello (dentro de la camisa)
PASSES = int(sys.argv[4]) if len(sys.argv) > 4 else 4

b = open(SRC, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + L]); binc = bytearray(b[28 + L:])
mesh = j['meshes'][0]
mesh_mats = {}
def walk(ni, P):
    n = j['nodes'][ni]; M = P @ render.node_mat(n)
    if 'mesh' in n: mesh_mats[n['mesh']] = M
    for c in n.get('children', []): walk(c, M)
for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
M0 = mesh_mats[0]; Minv = np.linalg.inv(M0)
def world(P): return (np.c_[P, np.ones(len(P))] @ M0.T)[:, :3]
def local(P): return (np.c_[P, np.ones(len(P))] @ Minv.T)[:, :3].astype(np.float32)
def append_bv(data, target=None):
    while len(binc) % 4: binc.append(0)
    d = {'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data)}
    if target: d['target'] = target
    j['bufferViews'].append(d); binc.extend(data); return len(j['bufferViews']) - 1
def add_acc(bvi, ctype, count, atype, arr=None):
    a = {'bufferView': bvi, 'componentType': ctype, 'count': int(count), 'type': atype}
    if arr is not None and atype == 'VEC3': a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
    j['accessors'].append(a); return len(j['accessors']) - 1
def write_pos(p, Pw):
    a = j['accessors'][p['attributes']['POSITION']]; bv = j['bufferViews'][a['bufferView']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); loc = local(Pw)
    binc[off:off + loc.nbytes] = loc.tobytes(); a['min'] = loc.min(0).tolist(); a['max'] = loc.max(0).tolist()
def set_idx(p, I):
    ii = I.astype(np.uint32).ravel(); p['indices'] = add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR')
names = [j['materials'][p['material']]['name'] for p in mesh['primitives']]
joints = j['skins'][0]['joints']; jn = {j['nodes'][ni]['name']: k for k, ni in enumerate(joints)}

# ================= 1. CABEZA: pulir el borde inferior
head = mesh['primitives'][names.index('GammaHead')]
HP = world(render.acc(j, binc, head['attributes']['POSITION'])); HI = render.acc(j, binc, head['indices']).astype(int).reshape(-1, 3)
ylo = HP[:, 1].min(); chin_band = ylo + 0.05
E = {}
for t in HI:
    for a_, c_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        k = (min(a_, c_), max(a_, c_)); E[k] = E.get(k, 0) + 1
rim = np.unique([v for k, n in E.items() if n == 1 for v in k if HP[v, 1] < chin_band])
print('cabeza intacta; vértices del borde de la mandíbula:', len(rim))
HPn = HP; ctr = np.array([HP[rim, 0].mean(), 0, HP[rim, 2].mean()])

# ================= 2. CUELLO: borrar el de Beta y construir un tubo nuevo
y_top = HPn[rim, 1]
ang = np.arctan2(HPn[rim, 2] - ctr[2], HPn[rim, 0] - ctr[0])
r_rim = np.linalg.norm((HPn[rim] - ctr)[:, [0, 2]], axis=1)
order = np.argsort(ang); ang_s, r_s, y_s = ang[order], r_rim[order], y_top[order]
def circ_smooth(v, w=21):
    k = np.ones(w) / w; return np.convolve(np.concatenate([v[-w:], v, v[:w]]), k, 'same')[w:-w]
r_s = circ_smooth(r_s); y_s = circ_smooth(y_s)
def interp_ang(a, vals):  # interpolación circular
    a = (a + np.pi) % (2 * np.pi) - np.pi
    xs = np.concatenate([ang_s - 2 * np.pi, ang_s, ang_s + 2 * np.pi]); vs = np.tile(vals, 3)
    return np.interp(a, xs, vs)
for nm in ('Skin', 'SkinShade'):
    for p in [p for p, n in zip(mesh['primitives'], names) if n == nm]:
        P = world(render.acc(j, binc, p['attributes']['POSITION'])); I = render.acc(j, binc, p['indices']).astype(int).reshape(-1, 3)
        keep = (P[I, 1] <= Y_COLLAR).all(1); print(f'{nm}: {(~keep).sum()} triángulos de cuello viejo eliminados'); set_idx(p, I[keep])
SEG = 36
th = np.linspace(-np.pi, np.pi, SEG, endpoint=False)
r_rim_t = interp_ang(th, r_s) * 0.95; y_rim_t = interp_ang(th, y_s) + 0.012
# perfil (factor de radio, y) de arriba hacia abajo: borde → bajo mandíbula → cuello → dentro de la camisa
prof = [(1.00, 0.0), (0.82, -0.014), (0.60, -0.032), (0.52, -0.05), (0.50, None), (0.50, None)]
V, N, J, Wt = [], [], [], []
ys_fixed = [Y_COLLAR + 0.03, Y_COLLAR]
for k, (fr, dy) in enumerate(prof):
    r = r_rim_t * fr
    y = y_rim_t + dy if dy is not None else np.full(SEG, ys_fixed.pop(0))
    x = ctr[0] + r * np.cos(th); z = ctr[2] + r * np.sin(th)
    V.append(np.c_[x, y, z])
    nrm = np.c_[np.cos(th), np.full(SEG, -0.6 if k < 3 else 0.0), np.sin(th)]; N.append(nrm / np.linalg.norm(nrm, axis=1, keepdims=True))
    w_head = 1.0 if k < 4 else (0.5 if k == 4 else 0.0)
    J.append(np.tile([jn['Head'], jn['Neck'], 0, 0], (SEG, 1))); Wt.append(np.tile([w_head, 1 - w_head, 0, 0], (SEG, 1)))
RINGS = len(prof)
V = np.concatenate(V); N = np.concatenate(N); J = np.concatenate(J).astype(np.uint16); Wt = np.concatenate(Wt).astype(np.float32)
r_top = r_rim_t; r_bot = r_rim_t * 0.48; yt = y_rim_t
I = []
for k in range(RINGS - 1):
    for s in range(SEG):
        a_, b_ = k * SEG + s, k * SEG + (s + 1) % SEG; c_, d_ = a_ + SEG, b_ + SEG
        I += [[a_, c_, b_], [b_, c_, d_]]
I = np.array(I)
import io
from PIL import Image
himg = j['images'][j['textures'][j['materials'][head['material']]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
hbv = j['bufferViews'][himg['bufferView']]; ho = hbv.get('byteOffset', 0)
TEX = np.asarray(Image.open(io.BytesIO(bytes(binc[ho:ho + hbv['byteLength']]))).convert('RGB'), dtype=np.float64) / 255
HUV = render.acc(j, binc, head['attributes']['TEXCOORD_0'])
chin = (HP[:, 1] < chin_band + 0.03)
cols = TEX[(np.mod(HUV[chin, 1], 1) * (TEX.shape[0] - 1)).astype(int), (np.mod(HUV[chin, 0], 1) * (TEX.shape[1] - 1)).astype(int)]
cols = cols[cols.mean(1) > 0.45]                       # solo piel iluminada, sin sombras ni pelo
srgb = np.median(cols, axis=0); lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
j['materials'].append({'name': 'NeckSkin', 'pbrMetallicRoughness': {'baseColorFactor': [*lin.tolist(), 1.0], 'metallicFactor': 0, 'roughnessFactor': 0.85}})
skin_mat = len(j['materials']) - 1; print('color de cuello (sRGB):', (srgb * 255).astype(int))
attrs = {}
for key, arr, ct, at in [('POSITION', local(V), 5126, 'VEC3'), ('NORMAL', (N @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32), 5126, 'VEC3'),
                         ('JOINTS_0', J, 5123, 'VEC4'), ('WEIGHTS_0', Wt, 5126, 'VEC4')]:
    attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
ii = I.astype(np.uint32).ravel()
mesh['primitives'].append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': skin_mat})
print(f'cuello nuevo: {len(I)} tris, radio arriba {r_top.mean()*100:.1f} cm, abajo {r_bot.mean()*100:.1f} cm, de y={yt.mean():.3f} a {Y_COLLAR}')

j['buffers'] = [{'byteLength': len(binc)}]
while len(binc) % 4: binc.append(0)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
print('escrito', OUT)
