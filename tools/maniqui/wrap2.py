"""Iteración 2+: shrinkwrap por zonas + suavizado + trasplante de cabeza de Gamma.
Uso: wrap2.py beta.glb gamma_30k.glb out.glb [MAXD_cm] [SMOOTH_PASSES] [CUT_FRAC]
Trabaja en el espacio de Beta (los huesos no se tocan); Gamma se escala a Beta."""
import json, struct, sys, io
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import render

BETA, GAMMA, OUT = sys.argv[1:4]
MAXD = float(sys.argv[4]) / 100 if len(sys.argv) > 4 else 0.05
SMOOTH = int(sys.argv[5]) if len(sys.argv) > 5 else 3
CUT_FRAC = float(sys.argv[6]) if len(sys.argv) > 6 else None   # altura relativa del corte de cuello (None = automático)

def srgb255(lin): return (render.srgb(np.array(lin[:3])) * 255)

# ======== GAMMA: vértices, uv, normales, índices, textura
gj, gb = render.load(GAMMA)
gp = gj['meshes'][0]['primitives'][0]
GP = render.acc(gj, gb, gp['attributes']['POSITION']); GN = render.acc(gj, gb, gp['attributes']['NORMAL'])
GUV = render.acc(gj, gb, gp['attributes']['TEXCOORD_0']); GI = render.acc(gj, gb, gp['indices']).astype(np.int64).reshape(-1, 3)
nd = gj['nodes'][gj['scenes'][0]['nodes'][0]]; GM = render.node_mat(nd)
GP = (np.c_[GP, np.ones(len(GP))] @ GM.T)[:, :3]; GN = GN @ GM[:3, :3].T
img_i = gj['images'][gj['textures'][gj['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
bv = gj['bufferViews'][img_i['bufferView']]; o = bv.get('byteOffset', 0)
tex_bytes = gb[o:o + bv['byteLength']]; TEX = np.asarray(Image.open(io.BytesIO(tex_bytes)).convert('RGB'), dtype=np.float64)
th, tw = TEX.shape[:2]
GC = TEX[(np.mod(GUV[:, 1], 1) * (th - 1)).astype(int), (np.mod(GUV[:, 0], 1) * (tw - 1)).astype(int)]  # color sRGB por vértice

# ======== BETA: primitivas
b = open(BETA, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + L]); binc = bytearray(b[28 + L:])
mesh_mats = {}
def walk(ni, P):
    n = j['nodes'][ni]; M = P @ render.node_mat(n)
    if 'mesh' in n: mesh_mats[n['mesh']] = (M, ni)
    for c in n.get('children', []): walk(c, M)
for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
prims = []
for mi, m in enumerate(j['meshes']):
    M, _ = mesh_mats[mi]
    for p in m['primitives']:
        a = j['accessors'][p['attributes']['POSITION']]; bvp = j['bufferViews'][a['bufferView']]
        off = bvp.get('byteOffset', 0) + a.get('byteOffset', 0)
        pos = np.frombuffer(binc, dtype=np.float32, count=a['count'] * 3, offset=off).reshape(-1, 3).astype(np.float64)
        idx = render.acc(j, binc, p['indices']).astype(np.int64).reshape(-1, 3)
        prims.append(dict(mesh=mi, p=p, off=off, n=a['count'], M=M, world=(np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3],
                          idx=idx, mat=j['materials'][p['material']]['name'], acc=a))
W = np.concatenate([p['world'] for p in prims]); bH = W[:, 1].max() - W[:, 1].min(); by0 = W[:, 1].min()
bc = ((W[:, 0].max() + W[:, 0].min()) / 2, (W[:, 2].max() + W[:, 2].min()) / 2)

# ---- Gamma → espacio de Beta
GP[:, 1] -= GP[:, 1].min(); gH = GP[:, 1].max(); s = bH / gH
gc = ((GP[:, 0].max() + GP[:, 0].min()) / 2, (GP[:, 2].max() + GP[:, 2].min()) / 2)
GP = (GP - [gc[0], 0, gc[1]]) * s + [bc[0], by0, bc[1]]
print(f'Beta altura {bH:.3f}  Gamma escalado x{s:.4f}')

# ======== Zonas de Gamma por color + altura
def matcol(name):
    for m in j['materials']:
        if m['name'] == name: return srgb255(m['pbrMetallicRoughness']['baseColorFactor'])
refs = {'skin': matcol('Skin'), 'hair': matcol('Hair'), 'white': matcol('Shirt'), 'navy': matcol('Tie'), 'dark': matcol('Coat')}
def chroma(c):  # independiente de la sombra horneada
    c = np.atleast_2d(c).astype(float) + 1; return c / c.sum(-1, keepdims=True)
names = list(refs); R = np.array([chroma(refs[k])[0] for k in names]); lum = np.array([refs[k].mean() for k in names])
D = ((chroma(GC)[:, None, :] - R[None]) ** 2).sum(-1) * 400 + ((GC.mean(1)[:, None] - lum[None]) / 255) ** 2 * 0.3
zone = np.array(names)[D.argmin(1)]
yrel = (GP[:, 1] - by0) / bH
dark = zone == 'dark'
zone[dark & (yrel < 0.10)] = 'shoes'
zone[dark & (yrel > 0.65)] = 'glasses'
zone[(zone == 'skin') & (yrel > 0.72) & (yrel < 0.80) & (np.abs(GP[:, 0] - bc[0]) > 0.12 * bH)] = 'skin'
for k in sorted(set(zone)): print('  zona', k, (zone == k).sum())

# ---- corte de cuello: banda de piel más angosta entre 0.55 y 0.72 de altura
if CUT_FRAC is None:
    # punto más bajo de la piel en la columna central arriba de la mitad: base del cuello en el cuello de la camisa
    m = (zone == 'skin') & (yrel > 0.5) & (np.abs(GP[:, 0] - bc[0]) < 0.08 * bH)
    CUT_FRAC = float(yrel[m].min()) + 0.005
cut_y = by0 + CUT_FRAC * bH
print(f'corte de cuello en {CUT_FRAC:.3f} de la altura (y={cut_y:.3f})')
zone[(zone == 'hair') & (GP[:, 1] < cut_y)] = 'dark'     # marrón abajo del cuello = gabardina en sombra

# ======== Proyección por zonas
ZONE_OF = {'Skin': 'skin', 'SkinShade': 'skin', 'Coat': 'dark', 'CoatDark': 'dark', 'Trousers': 'dark', 'Belt': 'dark',
           'Buckle': 'dark', 'Shoes': 'shoes', 'Sole': 'shoes', 'Shirt': 'white', 'Tie': 'navy'}
HEAD_MATS = {'Hair', 'Glasses', 'Brow', 'EyeWhite', 'Iris', 'Pupil', 'IrisLight', 'EyeLine', 'Mouth', 'Tongue', 'Teeth'}
def nearest(P, T, chunk=1500):
    idx = np.empty(len(P), dtype=int); d = np.empty(len(P))
    for i in range(0, len(P), chunk):
        Dm = ((P[i:i + chunk, None, :] - T[None]) ** 2).sum(-1); k = Dm.argmin(1)
        idx[i:i + chunk] = k; d[i:i + chunk] = np.sqrt(Dm[np.arange(len(k)), k])
    return idx, d
def adjacency(n, idx):
    nb = [[] for _ in range(n)]
    for a_, b_, c_ in idx: nb[a_] += [b_, c_]; nb[b_] += [a_, c_]; nb[c_] += [a_, b_]
    return nb
report = {}
for p in prims:
    P = p['world']; disp = np.zeros_like(P); keep = np.ones(len(P), bool)
    if p['mat'] in HEAD_MATS:
        keep[:] = False                      # toda la pieza es cabeza: se elimina
    elif p['mat'] in ZONE_OF:
        head = P[:, 1] > cut_y if p['mat'] in ('Skin', 'SkinShade') else np.zeros(len(P), bool)
        keep = ~head
        if p['mat'] in ('Coat', 'CoatDark'):
            sel = np.isin(zone, ['dark', 'white', 'navy']) & (yrel > 0.12) & (GP[:, 1] < cut_y + 0.01)
            T = GP[sel]; TN = GN[sel]; k, d = nearest(P, T); ok = (d < MAXD) & keep
            disp[ok] = T[k[ok]] + TN[k[ok]] * 0.004 - P[ok]
        elif p['mat'] in ('Skin', 'SkinShade'):
            T = GP[(zone == 'skin') & (GP[:, 1] < cut_y - 0.015)]      # piel de Gamma solo por debajo del corte (cuello)
            k, d = nearest(P, T); ok = (d < MAXD) & keep
            disp[ok] = T[k[ok]] - P[ok]
            neck = keep & (P[:, 1] > cut_y - 0.09)                        # franja del cuello: meterla hacia el eje
            ctr = np.array([bc[0], 0, P[neck, 2].mean() if neck.any() else bc[1]])
            tgt = P + disp; rad = tgt - ctr; rad[:, 1] = 0
            disp[neck] = (tgt[neck] - rad[neck] * 0.25) - P[neck]
        else:
            T = GP[(zone == ZONE_OF[p['mat']]) & (GP[:, 1] < cut_y + 0.01)]
            k, d = nearest(P, T); ok = (d < MAXD) & keep
            disp[ok] = T[k[ok]] - P[ok]
        if SMOOTH:
            nb = adjacency(len(P), p['idx'])
            for _ in range(SMOOTH):
                disp = np.array([(disp[i] + sum((disp[q] for q in nb[i]), np.zeros(3))) / (len(nb[i]) + 1) if nb[i] else disp[i] for i in range(len(P))])
        report[p['mat']] = dict(verts=int(len(P)), proyectados=round(float(ok.mean() if keep.any() else 0), 3),
                                dist_media_cm=round(float(d[ok].mean() * 100) if ok.any() else 0, 2),
                                dist_max_cm=round(float(d[ok].max() * 100) if ok.any() else 0, 2))
    p['new'] = P + disp; p['keep'] = keep
    # eliminar triángulos cuyos 3 vértices no se conservan
    tri_keep = keep[p['idx']].all(1) if p['mat'] in ('Skin', 'SkinShade') else keep[p['idx']].any(1)
    p['idx_new'] = p['idx'][tri_keep]
for k, v in report.items(): print(f"  {k:10s} {v}")

# ======== Escribir: posiciones, normales recalculadas, índices filtrados
def append_bv(data, target=None):
    while len(binc) % 4: binc.append(0)
    bvd = {'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data)}
    if target: bvd['target'] = target
    j['bufferViews'].append(bvd); binc.extend(data); return len(j['bufferViews']) - 1
def add_acc(bvi, ctype, count, atype, data_np=None):
    a = {'bufferView': bvi, 'componentType': ctype, 'count': int(count), 'type': atype}
    if data_np is not None and atype == 'VEC3': a['min'] = data_np.min(0).tolist(); a['max'] = data_np.max(0).tolist()
    j['accessors'].append(a); return len(j['accessors']) - 1
def vnormals(P, idx):
    N = np.zeros_like(P); fn = np.cross(P[idx[:, 1]] - P[idx[:, 0]], P[idx[:, 2]] - P[idx[:, 0]])
    for k in range(3): np.add.at(N, idx[:, k], fn)
    return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)
for p in prims:
    Minv = np.linalg.inv(p['M']); loc = (np.c_[p['new'], np.ones(len(p['new']))] @ Minv.T)[:, :3].astype(np.float32)
    binc[p['off']:p['off'] + loc.nbytes] = loc.tobytes(); p['acc']['min'] = loc.min(0).tolist(); p['acc']['max'] = loc.max(0).tolist()
    if 'NORMAL' in p['p']['attributes']:
        na = j['accessors'][p['p']['attributes']['NORMAL']]; nbv = j['bufferViews'][na['bufferView']]
        noff = nbv.get('byteOffset', 0) + na.get('byteOffset', 0)
        nrm = (vnormals(p['new'], p['idx']) @ np.linalg.inv(p['M'][:3, :3]).T).astype(np.float32)
        binc[noff:noff + nrm.nbytes] = nrm.tobytes()
    if len(p['idx_new']) != len(p['idx']):
        ii = p['idx_new'].astype(np.uint32).ravel(); bvi = append_bv(ii.tobytes(), 34963)
        p['p']['indices'] = add_acc(bvi, 5125, len(ii), 'SCALAR')

# ======== Trasplante de cabeza de Gamma (todo arriba del corte), pegada al hueso Head
skin = j['skins'][0]; joints = skin['joints']
head_joint = [i for i, ni in enumerate(joints) if j['nodes'][ni]['name'] == 'Head'][0]
face = GP[:, 1] > cut_y + 0.025
collar = ~face & (((zone == 'white') & (GC.mean(1) > 150)) | (zone == 'navy'))   # cuello de camisa y corbata de Gamma
above = GP[:, 1] > cut_y - 0.01 * bH
tri = GI[above[GI].any(1) & ~collar[GI].any(1)]     # borde inferior completo, sin el cuello de camisa
used = np.unique(tri); remap = -np.ones(len(GP), int); remap[used] = np.arange(len(used))
HP, HN, HUV = GP[used], GN[used], GUV[used]; HI = remap[tri]
M0, _ = mesh_mats[prims[0]['mesh']]; Minv = np.linalg.inv(M0)
HPl = (np.c_[HP, np.ones(len(HP))] @ Minv.T)[:, :3].astype(np.float32); HNl = (HN @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32)
JN = np.zeros((len(HP), 4), np.uint16); JN[:, 0] = head_joint; WN = np.zeros((len(HP), 4), np.float32); WN[:, 0] = 1
img_bv = append_bv(tex_bytes); j.setdefault('images', []).append({'bufferView': img_bv, 'mimeType': img_i.get('mimeType', 'image/jpeg')})
j.setdefault('samplers', []).append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497})
j.setdefault('textures', []).append({'source': len(j['images']) - 1, 'sampler': len(j['samplers']) - 1})
j['materials'].append({'name': 'GammaHead', 'pbrMetallicRoughness': {'baseColorTexture': {'index': len(j['textures']) - 1}, 'metallicFactor': 0, 'roughnessFactor': 0.85}})
attrs = {}
for key, arr, ct, at in [('POSITION', HPl, 5126, 'VEC3'), ('NORMAL', HNl, 5126, 'VEC3'), ('TEXCOORD_0', HUV.astype(np.float32), 5126, 'VEC2'),
                         ('JOINTS_0', JN, 5123, 'VEC4'), ('WEIGHTS_0', WN, 5126, 'VEC4')]:
    attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
ii = HI.astype(np.uint32).ravel()
j['meshes'][prims[0]['mesh']]['primitives'].append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'),
                                                     'material': len(j['materials']) - 1})
print(f'cabeza trasplantada: {len(HI)} tris, {len(HP)} verts, hueso Head={head_joint}')

j['buffers'] = [{'byteLength': len(binc)}]
while len(binc) % 4: binc.append(0)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
json.dump(dict(maxd_cm=MAXD * 100, smooth=SMOOTH, cut=CUT_FRAC, piezas=report), open(OUT + '.json', 'w'), indent=1)
print('escrito', OUT, round((28 + len(js) + len(binc)) / 1e6, 2), 'MB')
