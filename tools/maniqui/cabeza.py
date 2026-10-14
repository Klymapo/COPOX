"""Cabeza canónica paramétrica del maniquí: bola medida de Gamma, cara ligeramente aplanada, cuencas suaves
(para la textura deslizante de ojos), nariz, ranura de boca, orejas generadas y cuello recto nuevo.
Reemplaza las piezas Cabeza, Craneo y Cuello. Una sola cabeza cerrada, sin huecos; todo pesado a Head/Neck.
Historial: v2 horneado por raycast y v3 parche de Gamma fundido se descartaron (ruido de los lentes fundidos y escalones).
Uso: cabeza.py maniqui_in.glb out.glb"""
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
mesh_node = [i for i, n in enumerate(j['nodes']) if 'mesh' in n][0]; M0 = world[mesh_node]; Minv = np.linalg.inv(M0)
names = [p.get('extras', {}).get('pieza') for p in mesh['primitives']]
def prim(n):
    p = mesh['primitives'][names.index(n)]; A = p['attributes']
    P = render.acc(j, binc, A['POSITION']); P = (np.c_[P, np.ones(len(P))] @ M0.T)[:, :3]
    return p, P, render.acc(j, binc, p['indices']).astype(int).reshape(-1, 3)
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
HEAD = jn['Head']

# ================= 1. bola del cráneo (de la pieza 'Craneo') y cara de Gamma ('Cabeza')
_, CP, CI = prim('Craneo'); _, FP, FI = prim('Cabeza')
ctr_xz = np.array([(CP[:, 0].min() + CP[:, 0].max()) / 2, (CP[:, 2].min() + CP[:, 2].max()) / 2])
rx = (CP[:, 0].max() - CP[:, 0].min()) / 2; rz = (CP[:, 2].max() - CP[:, 2].min()) / 2
cy = FP[:, 1].min() + 0.55 * (FP[:, 1].max() - FP[:, 1].min())
top = CP[:, 1].max(); ry = top - cy
ctr = np.array([ctr_xz[0], cy, ctr_xz[1]])
y_chin = FP[:, 1].min() + 0.012
y_eye = ctr[1] + 0.02
print(f'bola: centro {ctr.round(3)} radios {rx*100:.1f}/{ry*100:.1f}/{rz*100:.1f} cm  barbilla y={y_chin:.3f}')

# perfil frontal de Gamma (plano de la cara) por altura
ys = np.arange(y_chin - 0.02, FP[:, 1].max() + 0.02, 0.01)
zf = []
for yy in ys:
    s = FP[(np.abs(FP[:, 1] - yy) < 0.012) & (np.abs(FP[:, 0] - ctr[0]) < 0.06)]
    zf.append(np.percentile(s[:, 2], 92) if len(s) > 10 else np.nan)
zf = np.array(zf); ok = ~np.isnan(zf); zf = np.interp(ys, ys[ok], zf[ok])
# plano de la cara: ajuste lineal del perfil (ignora el hundimiento de los ojos y el escalón de la ceja)
sel = (ys > y_chin + 0.02) & (ys < y_eye + 0.06) & ~((ys > y_eye - 0.13) & (ys < y_eye - 0.04));   # sin nariz/boca
sel &= zf > np.median(zf[sel]) - 0.03                                                   # sin huecos de la malla
A = np.polyfit(ys[sel], zf[sel], 1); zf = np.polyval(A, ys)
print(f'plano de cara: z = {A[0]:.3f}*y + {A[1]:.3f}')
z_face = lambda yy: np.interp(yy, ys, zf) - 0.003
# la bola se recalcula de frente a nuca: el frente toca el plano de la cara a la altura del ojo, la nuca queda donde estaba
z_back = CP[:, 2].min(); z_front = z_face(y_eye) + 0.006
rz = (z_front - z_back) / 2; ctr[2] = (z_front + z_back) / 2
print(f'bola ajustada: centro z {ctr[2]:.3f} rz {rz*100:.1f} cm (frente {z_front:.3f}, nuca {z_back:.3f})')
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def radius(n, y_est):
    """bola aplanada suavemente en la zona de la cara: nada de cortes duros"""
    r_ball = 1 / np.sqrt(((n / np.array([rx, ry, rz])) ** 2).sum())
    if n[2] <= 0.2: return r_ball
    r_plane = (z_face(y_est) - ctr[2]) / n[2]
    w = ss((n[2] - 0.2) / 0.5) * ss(((y_eye + 0.13) - y_est) / 0.10)      # ventana angular × ventana vertical (se funde 10 cm sobre la ceja)
    return r_ball - w * max(0.0, r_ball - r_plane)

# ================= 2. malla base lisa (SEG x RING)
def vnormals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
    for k in range(3): np.add.at(N, T[:, k], fn)
    return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)
SEG, RING = 128, 72
th = np.linspace(-np.pi, np.pi, SEG, endpoint=False); ph = np.linspace(0, np.pi, RING)
V, Nd, Rs = [], [], []
for p_ in ph:
    for t_ in th:
        n = np.array([np.sin(p_) * np.cos(t_), np.cos(p_), np.sin(p_) * np.sin(t_)])
        y_est = ctr[1] + n[1] * ry
        if y_est < ctr[1]: y_est = ctr[1] - (ctr[1] - y_est) / ry * (ctr[1] - y_chin)
        r = radius(n, y_est); pos = ctr + n * r
        if pos[1] < ctr[1]:
            f = (ctr[1] - pos[1]) / ry; pos[1] = ctr[1] - f * (ctr[1] - y_chin)
            w = 1 - 0.15 * f ** 2; pos[0] = ctr[0] + (pos[0] - ctr[0]) * w; pos[2] = ctr[2] + (pos[2] - ctr[2]) * w
        V.append(pos); Nd.append(n)
V = np.array(V); Nd = np.array(Nd)

# ================= 3. rasgos analíticos sobre la rejilla: cuencas de ojo (para la textura deslizante), nariz y boca
# medidas tomadas de Gamma: ojos a la altura y_eye, separados ~13 cm; nariz 7 cm bajo el ojo; boca 12 cm bajo el ojo
Dh = V - ctr; Dh /= np.linalg.norm(Dh, axis=1, keepdims=True)
def bump(cx, cyy, r, p=2.0):
    d = np.sqrt(((V[:, 0] - cx) / r) ** 2 + ((V[:, 1] - cyy) / r) ** 2); k = np.clip(1 - d, 0, 1)
    return (k ** p) * (3 - 2 * k ** p) * (Dh[:, 2] > 0.3)
disp = np.zeros(len(V))
for sx in (-1, 1): disp -= 0.005 * bump(ctr[0] + sx * 0.065, y_eye - 0.005, 0.040)     # cuencas suaves de 8 cm
disp += 0.014 * bump(ctr[0], y_eye - 0.07, 0.024, 1.5)                                  # nariz
disp -= 0.004 * np.clip(1 - np.abs(V[:, 0] - ctr[0]) / 0.045, 0, 1) ** 0.7 * np.exp(-((V[:, 1] - (y_eye - 0.125)) / 0.007) ** 2) * (Dh[:, 2] > 0.3)  # boca: ranura suave
V = V + Dh * disp[:, None]
I = []
for r in range(RING - 1):
    for s in range(SEG):
        a_, b_ = r * SEG + s, r * SEG + (s + 1) % SEG; c_, d_ = a_ + SEG, b_ + SEG
        I += [[a_, b_, c_], [b_, d_, c_]]
I = np.array(I)
cenV = V[I].mean(1); I = I[cenV[:, 1] > y_chin + 0.004]
N = vnormals(V, I)
print(f'cabeza nueva: {len(I)} tris')

# ================= 4. orejas: medio elipsoide pegado a la sien (Gamma las tiene en |x|≈rx, a la altura del ojo)
def ear(side):
    ax, ay, az = 0.026, 0.042, 0.020          # sale 2.2 cm, mide 6.8 cm de alto y 3.2 de fondo
    cx = ctr[0] + side * rx * 0.96; cyy = y_eye - 0.01; cz = ctr[2] - 0.01
    EP, EI = [], []
    S2, R2 = 16, 9
    for a in range(R2):
        pa = np.pi * a / (R2 - 1)              # 0 = punta exterior, pi = base pegada a la cabeza
        for s in range(S2):
            tb = 2 * np.pi * s / S2
            EP.append([cx + side * ax * np.cos(pa) - side * 0.004, cyy + ay * np.sin(pa) * np.cos(tb), cz + az * np.sin(pa) * np.sin(tb)])
    EP = np.array(EP)
    for a in range(R2 - 1):
        for s in range(S2):
            p0, p1 = a * S2 + s, a * S2 + (s + 1) % S2; p2, p3 = p0 + S2, p1 + S2
            EI += [[p0, p2, p1], [p1, p2, p3]] if side > 0 else [[p0, p1, p2], [p1, p3, p2]]
    EI = np.array(EI)
    return EP, vnormals(EP, EI), EI

# ================= 4b. cuello nuevo: tubo recto que entra en la cabeza (la cabeza nueva es más angosta abajo que la mandíbula de Gamma)
_, QP, QI = prim('Cuello')
base = QP[np.abs(QP[:, 1] - QP[:, 1].min()) < 1e-3]            # anillo inferior actual (empata con el torso)
qc = np.array([(base[:, 0].min() + base[:, 0].max()) / 2, 0, (base[:, 2].min() + base[:, 2].max()) / 2])
qrx, qrz = (base[:, 0].max() - base[:, 0].min()) / 2, (base[:, 2].max() - base[:, 2].min()) / 2
y0, y1, NR, NS = QP[:, 1].min(), y_chin + 0.055, 8, 36
NP, NJ, NW = [], [], []
for k in range(NR):
    yy = y0 + (y1 - y0) * k / (NR - 1); g = 1 + 0.06 * (k / (NR - 1))   # se ensancha 6 % al entrar en la cabeza
    wh = np.clip((yy - y0) / 0.04, 0, 1)
    for s_ in range(NS):
        a = 2 * np.pi * s_ / NS
        NP.append([qc[0] + qrx * g * np.cos(a), yy, qc[2] + qrz * g * np.sin(a)]); NJ.append([HEAD, jn['Neck'], 0, 0]); NW.append([wh, 1 - wh, 0, 0])
NP = np.array(NP); NI = []
for k in range(NR - 1):
    for s_ in range(NS):
        p0, p1 = k * NS + s_, k * NS + (s_ + 1) % NS; p2, p3 = p0 + NS, p1 + NS
        NI += [[p0, p1, p2], [p1, p3, p2]]
NI = np.array(NI); NNm = vnormals(NP, NI)
print(f'cuello nuevo: y {y0:.3f}..{y1:.3f}, {len(NI)} tris')

# ================= 5. escribir
keep_prims = [p for p, n in zip(mesh['primitives'], names) if n not in ('Cabeza', 'Craneo', 'Cuello')]
def add_piece(name, P, N_, I_, mat, J=None, W=None):
    Pl = (np.c_[P, np.ones(len(P))] @ Minv.T)[:, :3].astype(np.float32); Nl = (N_ @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32)
    J = (np.tile([HEAD, 0, 0, 0], (len(P), 1)) if J is None else np.array(J)).astype(np.uint16); W = (np.tile([1, 0, 0, 0], (len(P), 1)) if W is None else np.array(W)).astype(np.float32)
    attrs = {}
    for key, arr, ct, at in [('POSITION', Pl, 5126, 'VEC3'), ('NORMAL', Nl, 5126, 'VEC3'), ('JOINTS_0', J, 5123, 'VEC4'), ('WEIGHTS_0', W, 5126, 'VEC4')]:
        attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
    ii = I_.astype(np.uint32).ravel()
    keep_prims.append({'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': mat, 'extras': {'pieza': name}})
add_piece('Cabeza', V, N, I, gris)
add_piece('Cuello', NP, NNm, NI, gris, NJ, NW)
for side, nm in ((1, 'OrejaL'), (-1, 'OrejaR')):
    EP, EN, EI = ear(side); add_piece(nm, EP, EN, EI, gris)
mesh['primitives'] = keep_prims
j['buffers'] = [{'byteLength': len(binc)}]
while len(binc) % 4: binc.append(0)
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
print('escrito', OUT)
