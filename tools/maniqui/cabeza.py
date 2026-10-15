"""Cabeza canónica paramétrica del maniquí, estilo ALTH: "cajón redondeado" (superelipsoide) medido de las referencias
(tools/maniqui/medir_cara.py → JSON de proporciones relativas al ancho de cara), cuencas suaves (para la textura
deslizante de ojos), nariz de bloque, ranura de boca, orejas de bloque y cuello recto nuevo.
Reemplaza las piezas Cabeza, Craneo y Cuello. Una sola cabeza cerrada, sin huecos; todo pesado a Head/Neck.
Historial: v2 horneado por raycast y v3 parche de Gamma fundido se descartaron (ruido de los lentes fundidos y escalones).
Uso: cabeza.py maniqui_in.glb out.glb [rasgos.json]   (rasgos/gamma.json = medidas de la cara de Gamma con medir_gamma.py; sin JSON usa las de Theo)"""
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
    'boca': {'y_bajo_ojo': 0.36, 'ancho': 0.15, 'alto': 0.03},          # no medible en Theo (línea muy delgada): valor del estilo
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
a_back = R.get('craneo_ancho', 1.0) * W / 2
# el frente de la cara se queda donde estaba el plano de la cara de Gamma (a la altura del ojo); la nuca donde alcance
z_front = np.percentile(FP[(FP[:, 1] > y_chin) & (FP[:, 1] < y_chin + 0.7 * W) & (np.abs(FP[:, 0]) < 0.3 * W)][:, 2], 95)   # plano de la cara vieja (robusto a huecos)
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
    aa = a + (a_back - a) * ss((0.55 - n[2]) / 0.9)          # el cráneo es más ancho detrás de la cara (Gamma: ~1.24 W a la altura de las orejas)
    horiz = (abs(n[0] / aa) ** p_h + abs(n[2] / c) ** p_h) ** (1 / p_h)
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
    return ss((1.0 - d) / 0.6) * front
o, nz, bo = R['ojos'], R['nariz'], R['boca']
disp = np.zeros(len(V))
for sx in (-1, 1): disp -= R.get('ojos_hundidos', 0.0) * W * caja_suave(ctr[0] + sx * o['separacion'] * W / 2, y_eye, o['ancho'] * W * 1.1, o['alto'] * W * 1.1, 2.5)   # cuencas
nariz = nz.get('sale', 0.06) * W * caja_suave(ctr[0], y_eye - nz['y_bajo_ojo'] * W, nz['ancho'] * W * 1.1, nz['alto'] * W * 1.3, 2.6)         # nariz: bloque redondeado hacia +Z (sale medido de perfil)
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
    """oreja de Gamma: placa gruesa inclinada ~40° hacia atrás; de frente se ve 'sale' de ancho, de lado 'fondo' de largo"""
    e = R['orejas']; sale = e['sale'] * W; ang = np.radians(40)
    d = np.array([side * np.sin(ang), 0, -np.cos(ang)])                     # dirección de la placa (hacia afuera y atrás)
    nrm = np.array([side * np.cos(ang), 0, np.sin(ang)])                    # normal de la placa
    largo = sale / np.sin(ang) / 2; alto = e['alto'] * W / 2; grueso = 0.022 * W     # placa delgada como la de Gamma
    cyy = y_chin + e['y_sobre_barbilla'] * W
    zr = (z_front - e['detras_de_cara'] * W) if 'detras_de_cara' in e else ctr[2]
    base = np.array([ctr[0] + side * a_back * 0.95, cyy, zr])              # pegada al costado del cráneo
    largo = max(sale - (a_back - a), 0.08 * W) / np.sin(ang) / 2           # sólo lo que la oreja sale más allá del cráneo
    cen = base + d * largo * 0.9
    EP, EI = [], []; S2, R2 = 20, 10
    for k in range(R2):
        pa = np.pi * k / (R2 - 1)
        for s_ in range(S2):
            tb = 2 * np.pi * s_ / S2
            u = np.array([np.cos(pa), np.sin(pa) * np.cos(tb), np.sin(pa) * np.sin(tb)])
            rr = (abs(u[0]) ** 4 + abs(u[1]) ** 4 + abs(u[2]) ** 4) ** (-1 / 4)
            EP.append(cen + d * largo * u[0] * rr + np.array([0, alto, 0]) * u[1] * rr + nrm * grueso * u[2] * rr)
    EP = np.array(EP)
    for k in range(R2 - 1):
        for s_ in range(S2):
            p0, p1 = k * S2 + s_, k * S2 + (s_ + 1) % S2; p2, p3 = p0 + S2, p1 + S2
            EI += [[p0, p2, p1], [p1, p2, p3]]
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
def add_piece(name, P, N_, I_, mat, J=None, W=None, UV=None, targets=None):
    Pl = (np.c_[P, np.ones(len(P))] @ Minv.T)[:, :3].astype(np.float32); Nl = (N_ @ np.linalg.inv(M0[:3, :3]).T).astype(np.float32)
    J = (np.tile([HEAD, 0, 0, 0], (len(P), 1)) if J is None else np.array(J)).astype(np.uint16); W = (np.tile([1, 0, 0, 0], (len(P), 1)) if W is None else np.array(W)).astype(np.float32)
    attrs = {}
    for key, arr, ct, at in [('POSITION', Pl, 5126, 'VEC3'), ('NORMAL', Nl, 5126, 'VEC3'), ('JOINTS_0', J, 5123, 'VEC4'), ('WEIGHTS_0', W, 5126, 'VEC4')]:
        attrs[key] = add_acc(append_bv(arr.tobytes(), 34962), ct, len(arr), at, arr if at == 'VEC3' else None)
    if UV is not None: attrs['TEXCOORD_0'] = add_acc(append_bv(np.asarray(UV, np.float32).tobytes(), 34962), 5126, len(UV), 'VEC2')
    ii = I_.astype(np.uint32).ravel()
    prim_ = {'attributes': attrs, 'indices': add_acc(append_bv(ii.tobytes(), 34963), 5125, len(ii), 'SCALAR'), 'material': mat, 'extras': {'pieza': name}}
    if targets:      # morph targets (shape keys): deltas de posición en espacio local de la malla
        prim_['targets'] = [{'POSITION': add_acc(append_bv((d @ Minv[:3, :3].T).astype(np.float32).tobytes(), 34962), 5126, len(d), 'VEC3', (d @ Minv[:3, :3].T).astype(np.float32))} for d in targets]
    keep_prims.append(prim_)

# ================= 4c. boca: shape keys sobre la cabeza ("soplar" para Alastor y "abrir" para hablar)
y_mouth = y_eye - bo['y_bajo_ojo'] * W; mc = np.array([ctr[0], y_mouth])
d2 = np.sqrt(((V[:, 0] - mc[0]) / (0.16 * W)) ** 2 + ((V[:, 1] - mc[1]) / (0.11 * W)) ** 2); k_sop = ss(1 - d2) * front
soplar = np.zeros_like(V); soplar[:, 2] += 0.06 * W * k_sop; soplar[:, 0] -= 0.35 * (V[:, 0] - mc[0]) * k_sop          # labios hacia adelante y al centro
d3 = np.sqrt(((V[:, 0] - mc[0]) / (0.14 * W)) ** 2 + (np.clip(mc[1] - V[:, 1], 0, None) / (0.22 * W)) ** 2); k_ab = ss(1 - d3) * front * (V[:, 1] < mc[1] + 0.01 * W)
abrir = np.zeros_like(V); abrir[:, 1] -= 0.05 * W * k_ab; abrir[:, 2] -= 0.015 * W * k_ab                                  # mandíbula baja
mesh['extras'] = dict(mesh.get('extras', {}), targetNames=['boca_soplar', 'boca_abrir'])
add_piece('Cabeza', V, N, I, gris, targets=[soplar, abrir])

# ================= 4d. ojos: placas con textura deslizante (iris centrado; mover uv offset en Y = mirar arriba / "ojos en blanco")
from PIL import Image, ImageDraw
import io
TW, TH = 256, 512
im = Image.new('RGB', (TW, TH), (246, 244, 240)); dr = ImageDraw.Draw(im)
cx_, cy_ = TW // 2, TH // 2
# proporciones del iris medidas en Gamma (medir_gamma.py): ancho ≈ 0.60 del ojo, alto ≈ todo el ojo; la placa ocupa V 0.25..0.75 (alto = TH/2)
fi_w = o.get('iris_ancho', 0.6 * o['ancho']) / o['ancho']; fi_h = min(o.get('iris_alto', o['alto']) / o['alto'], 0.98)
rw, rh = int(0.5 * fi_w * TW), int(0.5 * fi_h * TH / 2)
dr.ellipse([cx_ - rw, cy_ - rh, cx_ + rw, cy_ + rh], fill=(70, 40, 20))                                  # iris café oscuro (Alastor)
dr.ellipse([cx_ - int(rw * 0.85), cy_ - int(rh * 0.55), cx_ + int(rw * 0.85), cy_ + int(rh * 0.95)], fill=(112, 64, 28))   # aclarado abajo
dr.ellipse([cx_ - int(rw * 0.48), cy_ - int(rh * 0.42), cx_ + int(rw * 0.48), cy_ + int(rh * 0.42)], fill=(20, 11, 5))    # pupila
dr.ellipse([cx_ - int(rw * 0.05), cy_ - int(rh * 0.62), cx_ + int(rw * 0.55), cy_ - int(rh * 0.12)], fill=(255, 255, 255))  # brillo (arriba-derecha, como Gamma)
# línea de pestañas arriba: banda delgada oscura en el borde superior de la placa (V 0.25 → y = TH/4)
dr.rectangle([0, TH // 4 - 2, TW, TH // 4 + int(0.06 * TH / 2)], fill=(40, 24, 14))
buf = io.BytesIO(); im.save(buf, 'PNG'); png = buf.getvalue()
j.setdefault('images', []).append({'bufferView': append_bv(png), 'mimeType': 'image/png', 'name': 'ojo_alastor'})
j.setdefault('samplers', []).append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071})
j.setdefault('textures', []).append({'source': len(j['images']) - 1, 'sampler': len(j['samplers']) - 1})
j['materials'].append({'name': 'Ojo', 'pbrMetallicRoughness': {'baseColorTexture': {'index': len(j['textures']) - 1}, 'metallicFactor': 0, 'roughnessFactor': 0.4}})
mat_ojo = len(j['materials']) - 1
def ojo(side):
    ew, eh = o['ancho'] * W, o['alto'] * W; ex = ctr[0] + side * o['separacion'] * W / 2
    # z de la superficie de la cabeza en el centro del ojo (vértice más cercano en x,y) + 2 mm
    k = np.argmin((V[:, 0] - ex) ** 2 + (V[:, 1] - y_eye) ** 2 + (V[:, 2] < ctr[2]) * 10); ez = V[k, 2] + 0.002
    SEG2 = 40; EP = [[ex, y_eye, ez]]; UV = [[0.5, 0.5]]; EI = []
    for s_ in range(SEG2):
        pe = float(np.interp(o.get('llenado_caja', 0.785), [0.785, 0.88, 0.93], [2.0, 3.0, 4.0])); pe = max(pe, 2.0)
        t = 2 * np.pi * s_ / SEG2; cx = np.sign(np.cos(t)) * abs(np.cos(t)) ** (2 / pe); cy = np.sign(np.sin(t)) * abs(np.sin(t)) ** (2 / pe)
        EP.append([ex + ew / 2 * cx, y_eye + eh / 2 * cy, ez - 0.004 * (cx * cx + cy * cy)])          # ligera curvatura hacia atrás en el borde
        UV.append([0.5 + 0.5 * cx, 0.5 - 0.25 * cy])                                                  # la placa usa la mitad central de la textura: hay 25 % de recorrido arriba y abajo
        EI.append([0, 1 + s_, 1 + (s_ + 1) % SEG2])
    EP = np.array(EP); EI = np.array(EI); EN = np.tile([0, 0, 1.0], (len(EP), 1))
    # la placa sigue la superficie de la cara: cada vértice toma la z del vértice frontal de la cabeza más cercano en (x, y) + 2.5 mm
    Vf = V[V[:, 2] > ctr[2]]
    for k_ in range(len(EP)):
        q = np.argmin((Vf[:, 0] - EP[k_, 0]) ** 2 + (Vf[:, 1] - EP[k_, 1]) ** 2); EP[k_, 2] = Vf[q, 2] + 0.0025
    return EP, EN, EI, np.array(UV)
for side, nm in ((1, 'OjoL'), (-1, 'OjoR')):
    EP, EN, EI, UV = ojo(side); add_piece(nm, EP, EN, EI, mat_ojo, UV=UV)
j['materials'].append({'name': 'Ceja', 'pbrMetallicRoughness': {'baseColorFactor': [0.16, 0.09, 0.04, 1.0], 'metallicFactor': 0, 'roughnessFactor': 0.9}})
mat_ceja = len(j['materials']) - 1
def ceja(side):
    cj = R['cejas']; bw, bh = cj['ancho'] * W, max(cj['alto'], 0.075) * W; bx = ctr[0] + side * o['separacion'] * W / 2; by = y_eye + cj['y_sobre_ojo'] * W
    k = np.argmin((V[:, 0] - bx) ** 2 + (V[:, 1] - by) ** 2 + (V[:, 2] < ctr[2]) * 10); bz = V[k, 2] + 0.004
    # bloque inclinado: más alto hacia el centro de la cara (ceño del estilo)
    pts = []
    for sx_, sy_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        ceno = cj.get('ceno', -0.3 * cj['alto']) * W
        x = bx + sx_ * bw / 2; y = by + sy_ * bh / 2 + (ceno / 2 if (sx_ * side) < 0 else -ceno / 2)       # ceño medido: el extremo interior baja
        pts.append([x, y, bz])
    P2 = np.array(pts + [[p[0], p[1], p[2] - 0.012] for p in pts])                                       # grosor hacia atrás (entra en la cabeza)
    F = np.array([[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2], [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]])
    return P2, vnormals(P2, F), F
for side, nm in ((1, 'CejaL'), (-1, 'CejaR')):
    EP, EN, EI = ceja(side); add_piece(nm, EP, EN, EI, mat_ceja)
# boca: placa delgada oscura con leve sonrisa de lado (estilo Theo); sigue a la cabeza y a los shape keys no (es rígida)
mw, mh = bo['ancho'] * W * 1.3, 0.022 * W; MP, MI = [], []
for i_ in range(9):
    u = i_ / 8; x = mc[0] - mw / 2 + mw * u; yb = y_mouth + 0.02 * W * (u - 0.5) + 0.03 * W * (u - 0.5) ** 2 * 0   # ligera asimetría
    k = np.argmin((V[:, 0] - x) ** 2 + (V[:, 1] - yb) ** 2 + (V[:, 2] < ctr[2]) * 10); zb = V[k, 2] + 0.003
    MP += [[x, yb + mh / 2, zb], [x, yb - mh / 2, zb]]
    if i_: MI += [[2 * i_ - 2, 2 * i_ - 1, 2 * i_], [2 * i_ - 1, 2 * i_ + 1, 2 * i_]]
MP = np.array(MP); MI = np.array(MI)
add_piece('Boca', MP, np.tile([0, 0, 1.0], (len(MP), 1)), MI, mat_ceja)
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
