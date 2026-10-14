"""Cuerpo limpio para el maniquí: torso, hombros, brazos superiores y piernas generados sobre el esqueleto.
Uso: cuerpo.py maniqui_in.glb maniqui_out.glb"""
import json, struct, sys
import numpy as np
sys.path.insert(0, '.')
import render

SRC, OUT = sys.argv[1], sys.argv[2]
b = open(SRC, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + L]); binc = bytearray(b[28 + L:])
mesh = j['meshes'][0]
world = {}
def walk(i, P):
    world[i] = P @ render.node_mat(j['nodes'][i])
    for c in j['nodes'][i].get('children', []): walk(c, world[i])
for r in j['scenes'][0]['nodes']: walk(r, np.eye(4))
joints = j['skins'][0]['joints']; jn = {j['nodes'][ni]['name']: k for k, ni in enumerate(joints)}
jp = {j['nodes'][ni]['name']: world[ni][:3, 3] for ni in joints}
mesh_node = [i for i, n in enumerate(j['nodes']) if 'mesh' in n][0]; M0 = world[mesh_node]; Minv = np.linalg.inv(M0)
names = [p.get('extras', {}).get('pieza') for p in mesh['primitives']]
def prim_pts(n):
    out = []
    for p, nm in zip(mesh['primitives'], names):
        if nm == n: P = render.acc(j, binc, p['attributes']['POSITION']); I = render.acc(j, binc, p['indices']).astype(int); out.append(P[np.unique(I)])
    return np.concatenate(out)
brazos = prim_pts('Brazos'); arm = (brazos[:, 1] > 0.40) & (brazos[:, 1] < 0.48) & (np.abs(brazos[:, 0]) > 0.10)
cuff_x = np.abs(brazos[arm, 0]).min()        # dónde empieza la piel del antebrazo (puño de la manga)
print('LowerArm', jp.get('LeftLowerArm'))
print('puño en |x| =', round(cuff_x, 3))

def append_bv(data, target=None):
    while len(binc) % 4: binc.append(0)
    d = {'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data)}
    if target: d['target'] = target
    j['bufferViews'].append(d); binc.extend(data); return len(j['bufferViews']) - 1
def add_acc(bvi, ct, n, at, arr=None):
    a = {'bufferView': bvi, 'componentType': ct, 'count': int(n), 'type': at}
    if arr is not None and at == 'VEC3': a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
    j['accessors'].append(a); return len(j['accessors']) - 1
gris = next(i for i, m in enumerate(j['materials']) if m['name'] == 'Maniqui')

P_BOX = 2.8   # exponente de la sección (2 = elipse, 3-4 = cajón redondeado). Estilo ALTH: cuerpos de bloques redondeados.
def loft(rings, weights, seg=32, cap_top=True, cap_bot=True, p=None):
    """rings: lista de (centro(3), rx, rz, eje_x(3), eje_z(3)[, p]); weights: lista de (joints4, w4) por anillo.
    La sección es una superelipse de exponente p (por anillo, o el global P_BOX): |x/rx|^p + |z/rz|^p = 1."""
    th = np.linspace(0, 2 * np.pi, seg, endpoint=False); V, N, J, W = [], [], [], []
    for ring, (jj, ww) in zip(rings, weights):
        c, rx, rz, ex, ez = ring[:5]; pe = ring[5] if len(ring) > 5 else (p if p is not None else P_BOX)
        for t in th:
            cx = np.sign(np.cos(t)) * abs(np.cos(t)) ** (2 / pe); cz = np.sign(np.sin(t)) * abs(np.sin(t)) ** (2 / pe)
            V.append(c + rx * cx * ex + rz * cz * ez); N.append(np.cos(t) * ex / rx + np.sin(t) * ez / rz)
            J.append(jj); W.append(ww)
    V = np.array(V); N = np.array(N); N /= np.linalg.norm(N, axis=1, keepdims=True)
    I = []
    for k in range(len(rings) - 1):
        for s in range(seg):
            a_, b_ = k * seg + s, k * seg + (s + 1) % seg; c_, d_ = a_ + seg, b_ + seg
            I += [[a_, c_, b_], [b_, c_, d_]]
    for cap, k, flip in ((cap_bot, 0, True), (cap_top, len(rings) - 1, False)):
        if not cap: continue
        c = rings[k][0]; ci = len(V); V = np.vstack([V, c]); N = np.vstack([N, [0, -1, 0] if flip else [0, 1, 0]]); J.append(weights[k][0]); W.append(weights[k][1])
        for s in range(seg):
            a_, b_ = k * seg + s, k * seg + (s + 1) % seg
            I.append([ci, a_, b_] if flip else [ci, b_, a_])
    I = np.array(I); fn = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]); N = np.zeros_like(V)
    for k in range(3): np.add.at(N, I[:, k], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    return V, N, np.array(J, np.uint16), np.array(W, np.float32), I

def wj(*pairs):
    jj = [0, 0, 0, 0]; ww = [0, 0, 0, 0]
    for k, (name, w) in enumerate(pairs): jj[k] = jn[name]; ww[k] = w
    return np.array(jj), np.array(ww)
EX, EY, EZ = np.eye(3)
pieces = []

# ---------- TORSO (caderas → base del cuello)
hips, spine, chest, neck = jp['Hips'], jp['Spine'], jp['Chest'], jp['Neck']
cz = 0.022
torso_prof = [  # (y, rx, rz, pesos)   · los 3 primeros anillos son la pelvis (misma pieza: sin costura ni labio)
    (0.236, 0.128, 0.074, wj(('Hips', 1))),
    (0.255, 0.136, 0.078, wj(('Hips', 1))),
    (0.275, 0.135, 0.077, wj(('Hips', 1))),
    (0.295, 0.130, 0.074, wj(('Hips', 1))),
    (0.330, 0.128, 0.074, wj(('Hips', 0.5), ('Spine', 0.5))),
    (0.370, 0.130, 0.076, wj(('Spine', 0.6), ('Chest', 0.4))),
    (0.410, 0.136, 0.078, wj(('Chest', 1))),
    (0.445, 0.140, 0.076, wj(('Chest', 1))),
    (0.475, 0.138, 0.074, wj(('Chest', 0.7), ('Neck', 0.3))),
    (0.500, 0.134, 0.072, wj(('Chest', 0.3), ('Neck', 0.7))),
    (0.518, 0.110, 0.064, wj(('Neck', 1))),
]
rings = [(np.array([0, y, cz]), rx, rz, EX, EZ) for y, rx, rz, _ in torso_prof]
Vt, Nt, Jt, Wt, It = loft(rings, [w for *_, w in torso_prof])
for v in range(len(Vt)):                     # borde inferior de la pelvis: cada mitad sigue un poco a su pierna (no se rasga al sentarse)
    if Vt[v][1] < 0.262:
        side = 'Left' if Vt[v][0] > 0 else 'Right'; f = np.clip((0.262 - Vt[v][1]) / 0.03, 0, 1) * 0.45
        jj, ww = wj(('Hips', 1 - f), (side + 'UpperLeg', f)); Jt[v] = jj; Wt[v] = ww
pieces.append(('Torso', (Vt, Nt, Jt, Wt, It)))

# ---------- PIERNAS (cadera → tobillo), una por lado
for side in ('Left', 'Right'):
    hip, knee, ankle = jp[side + 'UpperLeg'], jp[side + 'LowerLeg'], jp[side + 'Foot']
    sg = 1 if side == 'Left' else -1
    prof = [(hip + [-sg * 0.012, 0.03, 0], 0.056, 0.058, wj((side + 'UpperLeg', 1))),      # arranca dentro de la pelvis, un poco hacia el centro
            (hip + [-sg * 0.004, -0.02, 0], 0.060, 0.060, wj((side + 'UpperLeg', 1))),
            (knee + [0, 0.02, 0], 0.052, 0.052, wj((side + 'UpperLeg', 0.6), (side + 'LowerLeg', 0.4))),
            (knee - [0, 0.02, 0], 0.050, 0.050, wj((side + 'UpperLeg', 0.3), (side + 'LowerLeg', 0.7))),
            (ankle + [0, 0.03, 0], 0.046, 0.046, wj((side + 'LowerLeg', 1))),
            (ankle - [0, 0.005, 0], 0.044, 0.044, wj((side + 'LowerLeg', 0.5), (side + 'Foot', 0.5)))]
    rings = [(np.array(c), rx, rz, EX, EZ) for c, rx, rz, _ in prof]
    pieces.append(('Pierna' + side[0], loft(rings, [w for *_, w in prof])))

# ---------- HOMBRO + BRAZO SUPERIOR (hombro → puño de la manga), eje a lo largo del brazo
for side, sgn in (('Left', 1), ('Right', -1)):
    sh, ua = jp[side + 'Shoulder'], jp[side + 'UpperArm']
    la = jp.get(side + 'LowerArm', ua + [sgn * 0.09, 0, 0])
    axis = np.array([sgn, 0, 0.0]); ey = EY; ez = np.array([0, 0, 1.0])
    def at(x): return np.array([x, ua[1] + (x - ua[0]) * (la[1] - ua[1]) / max(abs(la[0] - ua[0]), 1e-6) * 0, ua[2]])
    xs = [ua[0] - sgn * 0.050, ua[0] - sgn * 0.022, ua[0] + sgn * 0.01, ua[0] + sgn * 0.05, la[0], la[0] + sgn * 0.02, sgn * (cuff_x + 0.012)]
    prof = [(at(xs[0]), 0.026, 0.026, wj((side + 'Shoulder', 0.5), (side + 'UpperArm', 0.5))),   # hombro: nace dentro del torso, redondeado
            (at(xs[1]), 0.040, 0.040, wj((side + 'Shoulder', 0.3), (side + 'UpperArm', 0.7))),
            (at(xs[2]), 0.044, 0.044, wj((side + 'UpperArm', 1))),                                 # brazos de bloque (Theo: ~0.08 de la altura de grueso)
            (at(xs[3]), 0.043, 0.043, wj((side + 'UpperArm', 1))),
            (at(xs[4]), 0.040, 0.040, wj((side + 'UpperArm', 0.5), (side + 'LowerArm', 0.5))),
            (at(xs[5]), 0.038, 0.038, wj((side + 'LowerArm', 1))),
            (at(xs[6]), 0.036, 0.036, wj((side + 'LowerArm', 1)))]
    rings = [(np.array(c), rx, rz, ey, ez) for c, rx, rz, _ in prof]
    pieces.append(('Brazo' + side[0], loft(rings, [w for *_, w in prof])))

# ---------- escribir: quitar Torso/Piernas viejos, agregar piezas nuevas
keep = [p for p, n in zip(mesh['primitives'], names) if n not in ('Torso', 'Piernas')]
for name, (V, N, J, W, I) in pieces:
    Vl = (np.c_[V, np.ones(len(V))] @ Minv.T)[:, :3].astype(np.float32); Nl = (N @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32)
    attrs = {}
    for key, arr, ct, at in [('POSITION', Vl, 5126, 'VEC3'), ('NORMAL', Nl, 5126, 'VEC3'), ('JOINTS_0', J, 5123, 'VEC4'), ('WEIGHTS_0', W, 5126, 'VEC4')]:
        attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
    ii = I.astype(np.uint32).ravel()
    keep.append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': gris, 'extras': {'pieza': name}})
    print(f'  {name}: {len(I)} tris')
mesh['primitives'] = keep
j['buffers'] = [{'byteLength': len(binc)}]
while len(binc) % 4: binc.append(0)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
print('escrito', OUT)
