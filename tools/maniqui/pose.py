"""Posa un GLB con skin en un instante de un clip y renderiza. Uso: pose.py in.glb clip t out.png"""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, '.')
import render

src, clip, t, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
j, b = render.load(src)
anim = [a for a in j['animations'] if a.get('name') == clip][0]
# pose local por nodo: empieza con la del archivo
local = {i: dict(t=n.get('translation', [0, 0, 0]), r=n.get('rotation', [0, 0, 0, 1]), s=n.get('scale', [1, 1, 1])) for i, n in enumerate(j['nodes'])}
def sample(sampler, t):
    T = render.acc(j, b, sampler['input']).ravel(); V = render.acc(j, b, sampler['output'])
    t = np.clip(t, T[0], T[-1]); k = np.searchsorted(T, t) - 1; k = np.clip(k, 0, len(T) - 2)
    f = (t - T[k]) / max(T[k + 1] - T[k], 1e-9); a, c = V[k], V[k + 1]
    if V.shape[1] == 4:  # slerp simple
        if np.dot(a, c) < 0: c = -c
        q = a * (1 - f) + c * f; return q / np.linalg.norm(q)
    return a * (1 - f) + c * f
for ch in anim['channels']:
    tgt = ch['target']; v = sample(anim['samplers'][ch['sampler']], t)
    key = {'translation': 't', 'rotation': 'r', 'scale': 's'}.get(tgt['path'])
    if key: local[tgt['node']][key] = v.tolist()
def lmat(i):
    l = local[i]; return render.node_mat({'translation': l['t'], 'rotation': l['r'], 'scale': l['s']})
world = {}
def walk(i, P):
    world[i] = P @ lmat(i)
    for c in j['nodes'][i].get('children', []): walk(c, world[i])
for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
skin = j['skins'][0]; ibm = render.acc(j, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
JM = np.array([world[ni] @ ibm[k] for k, ni in enumerate(skin['joints'])])
mesh_node = [i for i, n in enumerate(j['nodes']) if 'mesh' in n][0]; M = world[mesh_node] if 'skin' not in j['nodes'][mesh_node] else np.eye(4)
tris = []
texs = {}
import io
for ti, tx in enumerate(j.get('textures', [])):
    im = j['images'][tx['source']]; bv = j['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
    texs[ti] = np.asarray(Image.open(io.BytesIO(b[o:o + bv['byteLength']])).convert('RGB'), dtype=np.float64) / 255
for p in j['meshes'][0]['primitives']:
    A = p['attributes']; P = render.acc(j, b, A['POSITION']); J = render.acc(j, b, A['JOINTS_0']).astype(int); W = render.acc(j, b, A['WEIGHTS_0'])
    P4 = np.c_[P, np.ones(len(P))]; out_p = np.zeros((len(P), 3))
    for k in range(4):
        out_p += W[:, k:k + 1] * np.einsum('nij,nj->ni', JM[J[:, k]], P4)[:, :3]
    idx = render.acc(j, b, p['indices']).astype(int).reshape(-1, 3)
    mat = j['materials'][p['material']]; pbr = mat.get('pbrMetallicRoughness', {})
    col = render.srgb(np.array(pbr.get('baseColorFactor', [0.8, 0.8, 0.8, 1])[:3])); tex = uv = None
    if 'baseColorTexture' in pbr: tex = texs[pbr['baseColorTexture']['index']]; uv = render.acc(j, b, A['TEXCOORD_0'])[idx]
    tris.append((out_p[idx], col, uv, tex, None))
allv = np.concatenate([t[0].reshape(-1, 3) for t in tris]); bnd = (allv.min(0), allv.max(0))
views = [render.render(tris, y, bounds=bnd) for y in (0, 45, 90)]
sheet = Image.new('RGB', (420 * 3, 640), 'white')
for i, v in enumerate(views): sheet.paste(v, (420 * i, 0))
sheet.save(out); print(out)
