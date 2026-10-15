"""Cabeza canónica paramétrica del maniquí, estilo ALTH: "cajón redondeado" (superelipsoide) medido de las referencias
(tools/maniqui/medir_cara.py → JSON de proporciones relativas al ancho de cara), cuencas suaves (para la textura
deslizante de ojos), nariz de bloque, ranura de boca, orejas de bloque y cuello recto nuevo.
Reemplaza las piezas Cabeza, Craneo y Cuello. Una sola cabeza cerrada, sin huecos; todo pesado a Head/Neck.
Historial: v2 horneado por raycast y v3 parche de Gamma fundido se descartaron (ruido de los lentes fundidos y escalones).
Uso: cabeza.py maniqui_in.glb out.glb [rasgos.json]   (sin JSON usa las proporciones de Theo, refs/personajes/joven-rubio-4-vistas.jpg)"""
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

# ================= 1. proporciones (relativas al ANCHO DE CARA, W) medidas por medir_cara.py
R = {  # Theo de frente, joven-rubio-4-vistas.jpg (14 oct 2026)
    'alto_cara_sobre_ancho': 1.135, 'llenado_caja': 0.904, 'ancho_abajo': 0.962, 'radio_esquina_abajo': 0.081,
    'ojos': {'separacion': 0.578, 'ancho': 0.319, 'alto': 0.297, 'y_sobre_barbilla': 0.503},
    'cejas': {'y_sobre_ojo': 0.214, 'ancho': 0.341, 'alto': 0.130},
    'nariz': {'y_bajo_ojo': 0.230, 'ancho': 0.205, 'alto': 0.184},
    'boca': {'y_bajo_ojo': 0.45, 'ancho': 0.15, 'alto': 0.03},          # no medible en Theo (línea muy delgada): valor del estilo
    'orejas': {'sale': 0.10, 'alto': 0.26, 'fondo': 0.16, 'y_sobre_barbilla': 0.48},
    'fondo_sobre_alto': 0.92, 'craneo_sobre_cara': 1.12, 'ancho_cara_sobre_altura': 0.259,                 # lado: fondo/alto de la cara; cuánto sube el cráneo calvo sobre la línea del pelo
}
if len(sys.argv) > 3:
    J = json.load(open(sys.argv[3]))
    for k, v in J.items():
        if k in R and isinstance(v, dict): R[k].update(v)
        elif k == 'alto_sobre_ancho_cara': R['alto_cara_sobre_ancho'] = v
        elif not isinstance(v, dict) and not k.startswith('_'): R[k] = v
# ancho de cara del maniquí: el de la pieza 'Craneo' actual (viene de Gamma, consistente con el cuerpo)
_, CP, CI = prim('Craneo'); _, FP, FI = prim('Cabeza')
Htot = max(render.acc(j, binc, p['attributes']['POSITION'])[:, 1].max() for p in mesh['primitives'] if p.get('extras', {}).get('pieza') in ('Craneo', 'Cabeza'))
Htot = float(np.array([1, Htot]).max())      # altura del maniquí con la cabeza vieja (≈1.03 m); la cabeza nueva se escala a esta altura
W = R['ancho_cara_m'] if 'ancho_cara_m' in R else R.get('ancho_cara_sobre_altura', 0.316) * Htot   # ancho_cara_m manda si está
y_chin = R.get('barbilla_y', world[joints[HEAD]][1, 3] - 0.006)      # la barbilla queda justo arriba del hueso Head (en el estilo no se ve cuello)
Hc = R['alto_cara_sobre_ancho'] * W                   # barbilla → línea del pelo
Ht = R['craneo_sobre_cara'] * Hc                       # barbilla → coronilla (calvo)
D = R['fondo_sobre_alto'] * Hc                         # fondo de la cabeza
a, b, c = W / 2, Ht / 2, D / 2
# el frente de la cara se queda donde estaba el plano de la cara de Gamma (a la altura del ojo); la nuca donde alcance
z_front = np.percentile(FP[(np.abs(FP[:, 1] - (y_chin + R['ojos']['y_sobre_barbilla'] * W)) < 0.02) & (np.abs(FP[:, 0]) < 0.06 * W)][:, 2], 92)
ctr = np.array([(CP[:, 0].min() + CP[:, 0].max()) / 2, y_chin + b, z_front - c])
y_eye = y_chin + R['ojos']['y_sobre_barbilla'] * W
# exponente del superelipsoide a partir del llenado de la caja (n=2 → 0.785, n=3 → 0.88, n=4 → 0.93)
p_h = float(np.interp(R['llenado_caja'], [0.785, 0.88, 0.93, 0.97], [2.0, 3.0, 4.0, 6.0]))
p_v_bajo = float(np.interp(R['radio_esquina_abajo'], [0.03, 0.08, 0.2, 0.5], [6.0, 4.0, 2.5, 2.0]))
p_v_alto = 2.4                                         # la coronilla es más redonda
print(f'cabeza ALTH: W {W*100:.1f} cm, alto {Ht*100:.1f}, fondo {D*100:.1f}; exponentes h {p_h:.1f} abajo {p_v_bajo:.1f}; ojo en y={y_eye:.3f}')
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def radius(n):
    """radio del superelipsoide en la dirección n (semiejes a,b,c; exponente horizontal p_h, vertical según hemisferio)"""
    pv = p_v_bajo if n[1] < 0 else p_v_alto
    # mezcla: la sección horizontal usa p_h, la vertical pv
    horiz = (abs(n[0] / a) ** p_h + abs(n[2] / c) ** p_h) ** (1 / p_h)
    r = (horiz ** pv + abs(n[1] / b) ** pv) ** (-1 / pv)
    return r

# ================= 2. malla base (SEG x RING) sobre el superelipsoide; mandíbula un poco más angosta que la cara
SEG, RING = 128, 72
def vnormals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
    for k in range(3): np.add.at(N, T[:, k], fn)
    return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)
th = np.linspace(-np.pi, np.pi, SEG, endpoint=False); ph = np.linspace(0, np.pi, RING)
V = []
for p_ in ph:
    for t_ in th:
        n = np.array([np.sin(p_) * np.cos(t_), np.cos(p_), np.sin(p_) * np.sin(t_)])
        pos = ctr + n * radius(n)
        if pos[1] < y_eye:                                            # de los ojos a la barbilla se estrecha hasta ancho_abajo
            f = (y_eye - pos[1]) / (y_eye - y_chin); w = 1 - (1 - R['ancho_abajo']) * ss(f)
            pos[0] = ctr[0] + (pos[0] - ctr[0]) * w
        V.append(pos)
V = np.array(V)

# ================= 3. rasgos sobre la rejilla: cuencas (ojos), nariz de bloque, ranura de boca
Dh = V - ctr; Dh /= np.linalg.norm(Dh, axis=1, keepdims=True)
front = ss((Dh[:, 2] - 0.25) / 0.3)
def caja_suave(cx, cyy, w, h, p=4.0):
    """bulto con sección de superelipse (bloque redondeado): 1 en el centro, 0 fuera de la caja w×h"""
    d = (np.abs((V[:, 0] - cx) / (w / 2)) ** p + np.abs((V[:, 1] - cyy) / (h / 2)) ** p) ** (1 / p)
    return ss(1.15 - d) * front
o, nz, bo = R['ojos'], R['nariz'], R['boca']
disp = np.zeros(len(V))
for sx in (-1, 1): disp -= 0.012 * W * caja_suave(ctr[0] + sx * o['separacion'] * W / 2, y_eye, o['ancho'] * W * 1.1, o['alto'] * W * 1.1, 2.5)   # cuencas
nariz = 0.06 * W * caja_suave(ctr[0], y_eye - nz['y_bajo_ojo'] * W, nz['ancho'] * W, nz['alto'] * W, 5.0)                        # nariz: bloque hacia +Z
disp -= 0.012 * W * caja_suave(ctr[0], y_eye - bo['y_bajo_ojo'] * W, bo['ancho'] * W, bo['alto'] * W * 1.5, 3.0)                   # boca: ranura
V = V + Dh * disp[:, None]; V[:, 2] += nariz
I = []
for r in range(RING - 1):
    for s_ in range(SEG):
        a_, b_ = r * SEG + s_, r * SEG + (s_ + 1) % SEG; c_, d_ = a_ + SEG, b_ + SEG
        I += [[a_, b_, c_], [b_, d_, c_]]
I = np.array(I)
cenV = V[I].mean(1); I = I[cenV[:, 1] > y_chin + 0.004]
N = vnormals(V, I)
print(f'cabeza nueva: {len(I)} tris')

# ================= 4. orejas: bloque redondeado (superelipsoide) pegado a la sien
def ear(side):
    e = R['orejas']; ax, ay, az = e['sale'] * W, e['alto'] * W / 2, e['fondo'] * W / 2
    cyy = y_chin + e['y_sobre_barbilla'] * W
    # x de la sien a esa altura: radio del superelipsoide en dirección ±x
    nx = np.array([side, 0.0, 0.0]); cx = ctr[0] + side * radius(nx) * (1 - 0.3 * (1 - R['ancho_abajo']) * ss((y_eye - cyy) / (y_eye - y_chin)))
    cz = ctr[2] + 0.02 * W
    EP, EI = [], []; S2, R2 = 20, 10
    for k in range(R2):
        pa = np.pi * k / (R2 - 1)
        for s_ in range(S2):
            tb = 2 * np.pi * s_ / S2
            u = np.array([np.cos(pa), np.sin(pa) * np.cos(tb), np.sin(pa) * np.sin(tb)])
            rr = (abs(u[0]) ** 3 + abs(u[1]) ** 3 + abs(u[2]) ** 3) ** (-1 / 3)
            EP.append([cx + side * (ax * u[0] * rr - 0.4 * ax), cyy + ay * u[1] * rr, cz + az * u[2] * rr])
    EP = np.array(EP)
    for k in range(R2 - 1):
        for s_ in range(S2):
            p0, p1 = k * S2 + s_, k * S2 + (s_ + 1) % S2; p2, p3 = p0 + S2, p1 + S2
            EI += [[p0, p2, p1], [p1, p2, p3]] if side > 0 else [[p0, p1, p2], [p1, p3, p2]]
    EI = np.array(EI)
    return EP, vnormals(EP, EI), EI

# ================= 4b. cuello: bloque corto con la sección de la repisa de hombros del torso, que entra en la cabeza (estilo: casi sin cuello)
_, TP, TI = prim('Torso'); top_t = TP[:, 1].max()
sel = TP[np.abs(TP[:, 1] - top_t) < 2e-3]                              # anillo superior del torso
qc = np.array([(sel[:, 0].min() + sel[:, 0].max()) / 2, 0, (sel[:, 2].min() + sel[:, 2].max()) / 2])
qrx, qrz = R.get('cuello_rx', 0.085), R.get('cuello_rz', 0.058)                       # cuello: 17×11.6 cm, más angosto que la repisa de hombros
y0, y1, NR, NS = top_t - 0.03, y_chin + 0.03, 6, 48
NP, NJ, NW = [], [], []
for k in range(NR):
    yy = y0 + (y1 - y0) * k / (NR - 1); g = 1 - 0.08 * (k / (NR - 1))      # afina 8 % hacia la cabeza
    wh = np.clip((yy - top_t) / (y_chin - top_t), 0, 1)
    for s_ in range(NS):
        ang = 2 * np.pi * s_ / NS; cx_ = np.sign(np.cos(ang)) * abs(np.cos(ang)) ** (2 / 2.8); cz_ = np.sign(np.sin(ang)) * abs(np.sin(ang)) ** (2 / 2.8)
        NP.append([qc[0] + qrx * g * cx_, yy, qc[2] + qrz * g * cz_]); NJ.append([HEAD, jn['Neck'], 0, 0]); NW.append([wh, 1 - wh, 0, 0])
NP = np.array(NP); NI = []
for k in range(NR - 1):
    for s_ in range(NS):
        p0, p1 = k * NS + s_, k * NS + (s_ + 1) % NS; p2, p3 = p0 + NS, p1 + NS
        NI += [[p0, p1, p2], [p1, p3, p2]]
NI = np.array(NI); NNm = vnormals(NP, NI)
print(f'cuello: sección {qrx*100:.1f}×{qrz*100:.1f} cm, y {y0:.3f}..{y1:.3f}, {len(NI)} tris')

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
