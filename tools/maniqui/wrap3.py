"""Trasplante de faldones de gabardina y zapatos de Gamma sobre el resultado del shrinkwrap.
Uso: wrap3.py it4.glb beta_original.glb gamma_30k.glb out.glb
Los pesos de las piezas nuevas se copian del vértice más cercano de la pieza de Beta que reemplazan."""
import json, struct, sys, io
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import render

SRC, BETA0, GAMMA, OUT = sys.argv[1:5]
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}

# ---- Gamma en espacio de Beta (misma transformación que wrap2, a partir del Beta original)
bt = render.gather(BETA0); B = np.concatenate([t[0].reshape(-1, 3) for t in bt])
bH = B[:, 1].max() - B[:, 1].min(); by0 = B[:, 1].min(); bc = ((B[:, 0].max() + B[:, 0].min()) / 2, (B[:, 2].max() + B[:, 2].min()) / 2)
gj, gb = render.load(GAMMA); gp = gj['meshes'][0]['primitives'][0]
GP = render.acc(gj, gb, gp['attributes']['POSITION']); GN = render.acc(gj, gb, gp['attributes']['NORMAL'])
GUV = render.acc(gj, gb, gp['attributes']['TEXCOORD_0']); GI = render.acc(gj, gb, gp['indices']).astype(np.int64).reshape(-1, 3)
GM = render.node_mat(gj['nodes'][gj['scenes'][0]['nodes'][0]])
GP = (np.c_[GP, np.ones(len(GP))] @ GM.T)[:, :3]; GN = GN @ GM[:3, :3].T
GP[:, 1] -= GP[:, 1].min(); gH = GP[:, 1].max(); s = bH / gH
gc = ((GP[:, 0].max() + GP[:, 0].min()) / 2, (GP[:, 2].max() + GP[:, 2].min()) / 2)
GP = (GP - [gc[0], 0, gc[1]]) * s + [bc[0], by0, bc[1]]; yrel = (GP[:, 1] - by0) / bH
img_i = gj['images'][gj['textures'][gj['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
bv = gj['bufferViews'][img_i['bufferView']]; o = bv.get('byteOffset', 0)
TEX = np.asarray(Image.open(io.BytesIO(gb[o:o + bv['byteLength']])).convert('RGB'), dtype=np.float64); th, tw = TEX.shape[:2]
GC = TEX[(np.mod(GUV[:, 1], 1) * (th - 1)).astype(int), (np.mod(GUV[:, 0], 1) * (tw - 1)).astype(int)]
dark = GC.mean(1) < 90   # gabardina, pantalón, zapatos

# ---- Fuente (it4)
b = open(SRC, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + L]); binc = bytearray(b[28 + L:])
mesh_mats = {}
def walk(ni, P):
    n = j['nodes'][ni]; M = P @ render.node_mat(n)
    if 'mesh' in n: mesh_mats[n['mesh']] = M
    for c in n.get('children', []): walk(c, M)
for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
mesh = j['meshes'][0]; M0 = mesh_mats[0]; Minv = np.linalg.inv(M0)
def prim_data(p):
    A = p['attributes']; P = render.acc(j, binc, A['POSITION']); P = (np.c_[P, np.ones(len(P))] @ M0.T)[:, :3]
    idx = render.acc(j, binc, p['indices']).astype(np.int64).reshape(-1, 3)
    J = render.acc(j, binc, A['JOINTS_0']).astype(int); Wt = render.acc(j, binc, A['WEIGHTS_0'])
    return P, idx, J, Wt
byname = {}
for p in mesh['primitives']:
    byname.setdefault(j['materials'][p['material']]['name'], []).append(p)
def nearest(P, T, chunk=1500):
    idx = np.empty(len(P), dtype=int); d = np.empty(len(P))
    for i in range(0, len(P), chunk):
        Dm = ((P[i:i + chunk, None, :] - T[None]) ** 2).sum(-1); k = Dm.argmin(1)
        idx[i:i + chunk] = k; d[i:i + chunk] = np.sqrt(Dm[np.arange(len(k)), k])
    return idx, d
def append_bv(data, target=None):
    while len(binc) % 4: binc.append(0)
    d = {'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data)}
    if target: d['target'] = target
    j['bufferViews'].append(d); binc.extend(data); return len(j['bufferViews']) - 1
def add_acc(bvi, ctype, count, atype, arr=None):
    a = {'bufferView': bvi, 'componentType': ctype, 'count': int(count), 'type': atype}
    if arr is not None and atype == 'VEC3': a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
    j['accessors'].append(a); return len(j['accessors']) - 1
gamma_mat = [i for i, m in enumerate(j['materials']) if m['name'] == 'GammaHead'][0]

# ---- referencias de Beta: cinturón y pantalón
belt_y = np.mean([prim_data(p)[0][:, 1].mean() for p in byname['Belt']])
TR = np.concatenate([prim_data(p)[0] for p in byname['Trousers']])
coat_pts = [prim_data(p) for p in byname['Coat'] + byname['CoatDark']]
CP = np.concatenate([c[0] for c in coat_pts]); CJ = np.concatenate([c[2] for c in coat_pts]); CW = np.concatenate([c[3] for c in coat_pts])
coat_bottom = CP[:, 1].min()
shoe_pts = [prim_data(p) for p in byname['Shoes'] + byname['Sole']]
SP = np.concatenate([c[0] for c in shoe_pts]); SJ = np.concatenate([c[2] for c in shoe_pts]); SW = np.concatenate([c[3] for c in shoe_pts])
shoe_top = SP[:, 1].max()
print(f'cinturón y={belt_y:.3f}  gabardina baja hasta y={coat_bottom:.3f}  zapatos hasta y={shoe_top:.3f}')

def transplant(sel, srcP, srcJ, srcW, name):
    tri = GI[sel[GI].all(1)]
    used = np.unique(tri); remap = -np.ones(len(GP), int); remap[used] = np.arange(len(used))
    P, N, UV, I = GP[used], GN[used], GUV[used], remap[tri]
    kk, _ = nearest(P, srcP); Jn = srcJ[kk].astype(np.uint16); Wn = srcW[kk].astype(np.float32)
    Pl = (np.c_[P, np.ones(len(P))] @ Minv.T)[:, :3].astype(np.float32); Nl = (N @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32)
    attrs = {}
    for key, arr, ct, at in [('POSITION', Pl, 5126, 'VEC3'), ('NORMAL', Nl, 5126, 'VEC3'), ('TEXCOORD_0', UV.astype(np.float32), 5126, 'VEC2'),
                             ('JOINTS_0', Jn, 5123, 'VEC4'), ('WEIGHTS_0', Wn, 5126, 'VEC4')]:
        attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
    ii = I.astype(np.uint32).ravel()
    mesh['primitives'].append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': gamma_mat})
    print(f'  {name}: {len(I)} tris, {len(P)} verts')

def cut(prims, keep_fn):
    for p in prims:
        P, idx, _, _ = prim_data(p); keep = keep_fn(P); tri = idx[keep[idx].all(1)]
        ii = tri.astype(np.uint32).ravel(); p['indices'] = add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR')

# ---- Gamma: banda oscura entre zapatos y cinturón = faldones + pantalón; los pesos deciden qué es qué
band = dark & (GP[:, 1] > shoe_top - 0.005) & (GP[:, 1] < belt_y + 0.035)
shoes = dark & (GP[:, 1] < shoe_top + 0.01)
print('Gamma banda faldón+pantalón', band.sum(), 'zapatos', shoes.sum())
trs = [prim_data(p) for p in byname['Trousers']]
TP = np.concatenate([c[0] for c in trs]); TJ = np.concatenate([c[2] for c in trs]); TW = np.concatenate([c[3] for c in trs])
cut(byname['Coat'] + byname['CoatDark'], lambda P: P[:, 1] > belt_y - 0.005)
cut(byname['Trousers'], lambda P: P[:, 1] > belt_y - 0.005)
transplant(band, np.concatenate([CP[CP[:, 1] < belt_y + 0.04], TP]), np.concatenate([CJ[CP[:, 1] < belt_y + 0.04], TJ]),
           np.concatenate([CW[CP[:, 1] < belt_y + 0.04], TW]), 'faldones+pantalon')
cut(byname['Shoes'] + byname['Sole'], lambda P: np.zeros(len(P), bool))
transplant(shoes, SP, SJ, SW, 'zapatos')

j['buffers'] = [{'byteLength': len(binc)}]
while len(binc) % 4: binc.append(0)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
print('escrito', OUT, round((28 + len(js) + len(binc)) / 1e6, 2), 'MB')
