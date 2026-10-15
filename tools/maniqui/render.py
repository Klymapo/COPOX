"""Rasterizador mínimo de GLB (numpy + Pillow): 4 vistas ortográficas, pose de reposo."""
import json, struct, sys, io, math
import numpy as np
from PIL import Image

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def load(path):
    b = open(path, 'rb').read()
    L = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + L])
    off = 20 + L
    bl = struct.unpack('<I', b[off:off + 4])[0]
    binc = b[off + 8: off + 8 + bl]
    return j, binc

def acc(j, binc, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]); n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * n, offset=start)
    arr = np.lib.stride_tricks.as_strided(raw, shape=(a['count'], dt.itemsize * n), strides=(stride, 1)).copy()
    out = arr.view(dt).reshape(a['count'], n).astype(np.float64)
    if a.get('normalized'):
        out /= np.iinfo(dt).max
    return out

def node_mat(nd):
    if 'matrix' in nd:
        return np.array(nd['matrix']).reshape(4, 4).T
    t = nd.get('translation', [0, 0, 0]); r = nd.get('rotation', [0, 0, 0, 1]); s = nd.get('scale', [1, 1, 1])
    x, y, z, w = r
    R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                  [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                  [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    M = np.eye(4); M[:3, :3] = R * np.array(s); M[:3, 3] = t
    return M

def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)

def gather(path):
    j, binc = load(path)
    texs = {}
    for ti, t in enumerate(j.get('textures', [])):
        im = j['images'][t['source']]
        bv = j['bufferViews'][im['bufferView']]
        o = bv.get('byteOffset', 0)
        texs[ti] = np.asarray(Image.open(io.BytesIO(binc[o:o + bv['byteLength']])).convert('RGB'), dtype=np.float64) / 255
    tris = []  # (V(n,3,3), color per tri or None, uv(n,3,2), tex)
    def walk(ni, P):
        nd = j['nodes'][ni]; M = P @ node_mat(nd)
        if 'mesh' in nd:
            for p in j['meshes'][nd['mesh']]['primitives']:
                if p.get('mode', 4) != 4: continue
                pos = acc(j, binc, p['attributes']['POSITION'])
                pos = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
                idx = acc(j, binc, p['indices']).astype(int).ravel() if 'indices' in p else np.arange(len(pos))
                idx = idx.reshape(-1, 3)
                mat = j['materials'][p['material']] if 'material' in p else {}
                pbr = mat.get('pbrMetallicRoughness', {})
                col = srgb(np.array(pbr.get('baseColorFactor', [0.8, 0.8, 0.8, 1])[:3]))
                tex = uv = None
                if 'baseColorTexture' in pbr and 'TEXCOORD_0' in p['attributes']:
                    tex = texs[pbr['baseColorTexture']['index']]
                    uv = acc(j, binc, p['attributes']['TEXCOORD_0'])[idx]
                vc = None
                if 'COLOR_0' in p['attributes']:
                    vc = srgb(acc(j, binc, p['attributes']['COLOR_0'])[:, :3])[idx].mean(1)
                tris.append((pos[idx], col, uv, tex, vc))
        for c in nd.get('children', []):
            walk(c, M)
    for r in j['scenes'][j.get('scene', 0)]['nodes']:
        walk(r, np.eye(4))
    return tris

def render(tris, yaw_deg, W=420, H=640, bounds=None, unlit=False, depth=False):
    """unlit=True: color de textura sin sombreado (para medir). depth=True: devuelve (img, zbuffer, escala px/m)."""
    a = math.radians(yaw_deg)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    lo, hi = bounds
    ctr = (lo + hi) / 2; ext = hi - lo
    scale = 0.92 * min(W / max(ext[0], ext[2]), H / ext[1])
    img = np.ones((H, W, 3)) * np.array([0.93, 0.92, 0.90])
    zb = np.full((H, W), -np.inf)
    light = np.array([0.35, 0.55, 0.75]); light /= np.linalg.norm(light)
    for V, col, uv, tex, vc in tris:
        P = (V - ctr) @ Ry.T
        X = P[..., 0] * scale + W / 2; Y = -P[..., 1] * scale + H / 2; Z = P[..., 2]
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nl = np.linalg.norm(n, axis=1) + 1e-12; n = n / nl[:, None]
        shade = np.ones(len(P)) if unlit else 0.42 + 0.58 * np.abs(n @ light)
        for t in range(len(P)):
            x0, x1 = int(max(0, np.floor(X[t].min()))), int(min(W - 1, np.ceil(X[t].max())))
            y0, y1 = int(max(0, np.floor(Y[t].min()))), int(min(H - 1, np.ceil(Y[t].max())))
            if x1 < x0 or y1 < y0: continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
            (ax, bx, cx), (ay, by, cy) = X[t], Y[t]
            d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-12: continue
            w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
            w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / d
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not m.any(): continue
            z = w0 * Z[t, 0] + w1 * Z[t, 1] + w2 * Z[t, 2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            m &= z > sub
            if not m.any(): continue
            sub[m] = z[m]
            if tex is not None:
                u = w0 * uv[t, 0, 0] + w1 * uv[t, 1, 0] + w2 * uv[t, 2, 0]
                v = w0 * uv[t, 0, 1] + w1 * uv[t, 1, 1] + w2 * uv[t, 2, 1]
                th, tw = tex.shape[:2]
                px = tex[(np.mod(v[m], 1) * (th - 1)).astype(int), (np.mod(u[m], 1) * (tw - 1)).astype(int)]
            else:
                c = vc[t] if vc is not None else col
                px = np.broadcast_to(c, (m.sum(), 3))
            img[y0:y1 + 1, x0:x1 + 1][m] = px * shade[t]
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return (out, zb, scale) if depth else out

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    tris = gather(src)
    if len(sys.argv) > 3 and sys.argv[3] == 'zup':
        tris = [(np.stack([t[0][..., 0], t[0][..., 2], -t[0][..., 1]], -1),) + t[1:] for t in tris]
    allv = np.concatenate([t[0].reshape(-1, 3) for t in tris])
    b = (allv.min(0), allv.max(0))
    views = [render(tris, y, bounds=b) for y in (0, 45, 90, 180)]
    sheet = Image.new('RGB', (420 * 4, 640), 'white')
    for i, v in enumerate(views):
        sheet.paste(v, (420 * i, 0))
    sheet.save(out)
    print(out, len(sum([list(t[0]) for t in tris], [])), 'tris', b)
