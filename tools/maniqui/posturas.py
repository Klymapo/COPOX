"""Posturas y gestos de las láminas de referencia (Drive: EL PESO DE LOS NOMBRES / REFERENCIAS POSTURAS, GESTOS Y ERGONOMÍA)
como rotaciones de huesos sobre el esqueleto de Beta. Los huesos no tienen rotación de reposo: los ejes locales en reposo
son los del mundo (Y arriba, frente +Z, brazo izquierdo hacia +X). Convención (grados, lado IZQUIERDO; el derecho se espeja):
  UpperArm  z<0 baja el brazo · y<0 lo lleva al frente · y>0 atrás        LowerArm  y<0 dobla el codo hacia el frente/arriba
  Spine/Chest/Neck/Head  x>0 inclina hacia adelante · z ladea · y gira  UpperLeg  x<0 levanta la pierna al frente · z>0 abre
  LowerLeg  x>0 dobla la rodilla hacia atrás                               Hand  y<0 dobla la muñeca hacia la palma
Uso: posturas.py in.glb out.glb [--render carpeta --refs carpeta_laminas]
Escribe un clip por pose ("P15_1_Neutral"…): 2 llaves, de reposo a la pose en 0.3 s (Godot se queda en la última)."""
import json, struct, sys, os
import numpy as np
sys.path.insert(0, '.')
import render

def L(**kw): return kw
BASE = dict(UpperArm=(0, 0, -70), LowerArm=(0, -10, 0))          # brazos abajo, relajados
POSES = {
    # ---- 15 · Gestos / actitud base
    'P15_1_Neutral':   dict(L=BASE, R=BASE),
    'P15_2_Curioso':   dict(C=dict(Spine=(10, 0, 0), Chest=(6, 0, 0), Neck=(6, 0, 8), Head=(8, 0, 14)), IK=dict(mano=(0.05, 0.33, -0.10), codo=(1, -0.2, -0.6))),
    'P15_3_Timido':    dict(C=dict(Spine=(6, 0, 0), Chest=(6, 0, 0), Neck=(8, 0, -4), Head=(14, 0, -8)),
                            L=dict(Shoulder=(0, 0, 8), UpperLeg=(0, 0, -3)), R=dict(Shoulder=(0, 0, 8), UpperLeg=(0, 0, -3)), IK=dict(mano=(0.035, 0.32, 0.13), codo=(1, -0.3, 0.2))),
    'P15_4_Seguro':    dict(C=dict(Spine=(-4, 0, 0), Chest=(-5, 0, 0), Head=(-8, 0, 0)),
                            L=dict(UpperLeg=(0, 0, 5)), R=dict(UpperLeg=(0, 0, 5)), IK=dict(mano=(0.15, 0.30, 0.0), codo=(1, 0, -0.4))),
    'P15_5_Orgulloso': dict(C=dict(Spine=(-8, 0, 0), Chest=(-6, 0, 0), Neck=(-4, 0, 0), Head=(-12, 0, 6)),
                            R=dict(UpperLeg=(-8, 0, 4), LowerLeg=(6, 0, 0)), IK=dict(mano=(0.15, 0.31, -0.01), codo=(1, 0, -0.5))),
    # ---- 16 · Gestos / positivos
    'P16_1_Feliz':     dict(C=dict(Spine=(-4, 6, 0), Chest=(-4, 0, -4), Head=(-6, 0, 10)),
                            L=dict(UpperArm=(0, -15, -15), LowerArm=(0, -25, 10)), R=dict(UpperArm=(0, -15, -22), LowerArm=(0, -20, 10), UpperLeg=(14, 0, 4), LowerLeg=(55, 0, 0))),
    'P16_2_Emocionado': dict(C=dict(Spine=(4, 0, 0), Head=(-4, 0, -6)),
                            L=dict(UpperLeg=(-45, 0, 2), LowerLeg=(65, 0, 0)), IK=dict(mano=(0.09, 0.47, 0.16), codo=(0.6, -1, 0))),
    'P16_3_Aliviado':  dict(C=dict(Spine=(-5, 0, 0), Chest=(-3, 0, 0), Head=(-12, 0, 6)),
                            L=dict(Shoulder=(0, 0, -6), UpperArm=(0, 8, -74), LowerArm=(0, -6, 0)), R=dict(Shoulder=(0, 0, -6), UpperArm=(0, 8, -74), LowerArm=(0, -6, 0))),
    'P16_4_Agradecido': dict(C=dict(Spine=(10, 0, 0), Chest=(6, 0, 0), Head=(10, 0, 6)),
                            IK=dict(mano=(0.035, 0.33, 0.12), codo=(1, -0.3, 0.2))),
    'P16_5_Jugueton':  dict(C=dict(Hips=(0, 0, -4), Spine=(0, 0, 8), Chest=(0, 0, 6), Head=(0, 0, -14)),
                            L=dict(UpperArm=(0, 0, -18), LowerArm=(0, -15, 0)), R=dict(UpperArm=(0, 10, -12), LowerArm=(0, -10, 0), UpperLeg=(18, 0, 6), LowerLeg=(60, 0, 0))),
    # ---- 17 · Gestos / negativos
    'P17_1_Triste':    dict(C=dict(Spine=(8, 0, 0), Chest=(4, 0, 0), Neck=(8, 0, 0), Head=(18, 0, 0)),
                            L=dict(Shoulder=(0, 0, -6), UpperArm=(0, -8, -74), LowerArm=(0, -8, 0)), R=dict(Shoulder=(0, 0, -6), UpperArm=(0, -8, -74), LowerArm=(0, -8, 0))),
    'P17_2_Molesto':   dict(C=dict(Spine=(4, 0, 0), Chest=(3, 0, 0), Head=(8, 0, 0)),
                            L=dict(UpperArm=(0, 10, -66), LowerArm=(0, -12, 0), UpperLeg=(0, 0, 5)), R=dict(UpperArm=(0, 10, -66), LowerArm=(0, -12, 0), UpperLeg=(0, 0, 5))),
    'P17_3_Asustado':  dict(C=dict(Spine=(6, 0, 0), Neck=(-4, 0, 0), Head=(-6, 0, 8)),
                            L=dict(Shoulder=(0, 0, 10), UpperLeg=(-8, 0, -3), LowerLeg=(12, 0, 0)), R=dict(Shoulder=(0, 0, 10), UpperLeg=(-4, 0, -3), LowerLeg=(8, 0, 0)),
                            IK=dict(mano=(0.045, 0.45, 0.13), codo=(0.3, -1, 0))),
    'P17_4_Confundido': dict(C=dict(Neck=(0, 0, 6), Head=(0, 0, 12)), L=BASE,
                            IK=dict(mano_R=(0.15, 0.66, 0.06), codo_R=(1, -0.4, -0.3))),
    'P17_5_Cansado':   dict(C=dict(Spine=(10, 0, 0), Chest=(4, 0, 0), Neck=(8, 0, -6), Head=(12, 0, -14)),
                            L=dict(Shoulder=(0, 0, -8), UpperArm=(0, -10, -78), LowerArm=(0, -5, 0), UpperLeg=(-8, 0, 0), LowerLeg=(12, 0, 0)),
                            R=dict(Shoulder=(0, 0, -8), UpperArm=(0, -10, -78), LowerArm=(0, -5, 0), UpperLeg=(-8, 0, 0), LowerLeg=(12, 0, 0))),
    # ---- 18 · Reacciones sociales
    'P18_1_SaludoSuave': dict(C=dict(Head=(0, 0, 6)), L=BASE, IK=dict(mano_R=(0.25, 0.58, 0.05), codo_R=(1, -1, 0.1))),
    'P18_2_SorpresaLeve': dict(C=dict(Spine=(-6, 0, 0), Head=(-6, 0, 0)),
                            L=dict(UpperArm=(0, -10, -55), LowerArm=(0, -30, 0)), R=dict(UpperArm=(0, -10, -55), LowerArm=(0, -30, 0))),
    'P18_3_Duda':      dict(C=dict(Neck=(4, 0, 6), Head=(6, 0, 10)),
                            IK=dict(mano_R=(0.03, 0.56, 0.14), codo_R=(0.5, -1, 0.2), mano_L=(-0.02, 0.38, 0.13), codo_L=(1, -0.5, 0))),
    'P18_4_EscuchaAtenta': dict(C=dict(Spine=(8, 0, 0), Neck=(2, 0, 6), Head=(4, 0, 12)), IK=dict(mano=(0.05, 0.33, -0.10), codo=(1, -0.2, -0.6))),
    'P18_5_Verguenza': dict(C=dict(Spine=(6, 0, 0), Neck=(8, 0, -6), Head=(14, 0, -10)),
                            L=dict(Shoulder=(0, 0, 8), UpperLeg=(0, 0, -4)), R=dict(Shoulder=(0, 0, 8), UpperLeg=(0, 0, -4)), IK=dict(mano=(0.035, 0.32, 0.13), codo=(1, -0.3, 0.2))),
    # ---- 19 · Gestos serios
    'P19_1_NeutralSerio': dict(L=dict(UpperArm=(0, 0, -66), LowerArm=(0, -5, 0)), R=dict(UpperArm=(0, 0, -66), LowerArm=(0, -5, 0))),
    'P19_2_Observador': dict(C=dict(Head=(4, 0, 0)), IK=dict(mano_R=(0.03, 0.56, 0.14), codo_R=(0.4, -1, 0.1), mano_L=(-0.03, 0.40, 0.12), codo_L=(1, -0.6, 0))),
    'P19_3_Reservado': dict(C=dict(Head=(5, 0, 0)), IK=dict(mano_L=(-0.04, 0.41, 0.13), mano_R=(-0.04, 0.43, 0.135), codo=(1, -0.6, 0.3))),
    'P19_4_Determinado': dict(C=dict(Chest=(-3, 0, 0), Head=(4, 0, 0)),
                            L=dict(UpperArm=(0, 0, -60), LowerArm=(0, -15, 0), UpperLeg=(0, 0, 6)), R=dict(UpperArm=(0, 0, -60), LowerArm=(0, -15, 0), UpperLeg=(0, 0, 6))),
    'P19_5_Impasible': dict(L=dict(UpperArm=(0, 0, -72), LowerArm=(0, -3, 0)), R=dict(UpperArm=(0, 0, -72), LowerArm=(0, -3, 0))),
    # ---- 20 · Gestos intimidantes
    'P20_1_Desafiante': dict(C=dict(Chest=(4, 0, 0), Head=(10, 0, 0)),
                            L=dict(UpperArm=(0, 4, -64), LowerArm=(0, -10, 0), UpperLeg=(0, 0, 5)), R=dict(UpperArm=(0, 4, -64), LowerArm=(0, -10, 0), UpperLeg=(0, 0, 5))),
    'P20_2_Amenazante': dict(C=dict(Spine=(12, 0, 0), Chest=(4, 0, 0), Head=(-6, 0, 0)),
                            L=dict(UpperArm=(0, -25, -45), LowerArm=(0, -40, 0), UpperLeg=(-6, 0, 8), LowerLeg=(10, 0, 0)), R=dict(UpperArm=(0, -25, -45), LowerArm=(0, -40, 0), UpperLeg=(-6, 0, 8), LowerLeg=(10, 0, 0))),
    'P20_3_Dominante': dict(C=dict(Spine=(-4, 0, 0), Chest=(-4, 0, 0), Head=(-6, 0, 0)), L=dict(UpperLeg=(0, 0, 7)), R=dict(UpperLeg=(0, 0, 7)),
                            IK=dict(mano=(0.15, 0.30, 0.0), codo=(1, 0, -0.4))),
    'P20_4_Frio':      dict(C=dict(Head=(3, 10, 0)), L=dict(UpperArm=(0, 0, -72), LowerArm=(0, -3, 0)), R=dict(UpperArm=(0, 0, -72), LowerArm=(0, -3, 0))),
    'P20_5_Satisfecho': dict(C=dict(Hips=(0, 0, 4), Spine=(0, 0, -3), Head=(-6, 0, -8)), L=BASE, IK=dict(mano_R=(0.15, 0.30, 0.0), codo_R=(1, 0, -0.4))),
}

def quat(rx, ry, rz):
    """rotación R = Rz·Ry·Rx (grados) → cuaternión glTF [x, y, z, w]"""
    def q_ax(ax, a):
        a = np.radians(a) / 2; v = np.zeros(4); v[ax] = np.sin(a); v[3] = np.cos(a); return v
    def mul(p, q):
        x1, y1, z1, w1 = p; x2, y2, z2, w2 = q
        return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                         w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
    return mul(mul(q_ax(2, rz), q_ax(1, ry)), q_ax(0, rx))

def huesos(pose):
    """{nombre_de_nodo: cuaternión} con el lado derecho espejado (x igual, y y z cambian de signo)"""
    out = {}
    for b, (rx, ry, rz) in pose.get('C', {}).items(): out[b] = quat(rx, ry, rz)
    for side, sgn in (('L', 1), ('R', -1)):
        for b, (rx, ry, rz) in pose.get(side, {}).items():
            out[('Left' if side == 'L' else 'Right') + b] = quat(rx, sgn * ry, sgn * rz)
    return out

def _q_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def _q_from(a, b_):
    """cuaternión del arco más corto que lleva el vector a al vector b"""
    a = a / np.linalg.norm(a); b_ = b_ / np.linalg.norm(b_); c = np.cross(a, b_); d = np.dot(a, b_)
    if d < -0.9999:
        ax = np.cross(a, [0, 1, 0]); ax = ax if np.linalg.norm(ax) > 1e-6 else np.cross(a, [1, 0, 0]); ax /= np.linalg.norm(ax); return np.array([*ax, 0.0])
    q = np.array([*c, 1 + d]); return q / np.linalg.norm(q)
def mundo(j, rot):
    idx = {n['name']: i for i, n in enumerate(j['nodes'])}
    local = {i: dict(t=n.get('translation', [0, 0, 0]), r=n.get('rotation', [0, 0, 0, 1]), s=n.get('scale', [1, 1, 1])) for i, n in enumerate(j['nodes'])}
    for nm, q in rot.items(): local[idx[nm]]['r'] = list(q)
    world = {}
    def walk(i, P):
        world[i] = P @ render.node_mat({'translation': local[i]['t'], 'rotation': local[i]['r'], 'scale': local[i]['s']})
        for c in j['nodes'][i].get('children', []): walk(c, world[i])
    for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
    return world, idx
def resolver(j, pose):
    """rotaciones finales: FK de la pose + IK de brazos (mano a un punto del espacio de la cadera, codo hacia 'codo')"""
    rot = huesos(pose)
    if 'IK' not in pose: return rot
    ik = pose['IK']
    for side, sgn in (('Left', 1), ('Right', -1)):
        m_ = ik.get('mano_' + side[0], ik.get('mano'))
        if m_ is None: continue                                     # IK sólo de un lado
        tgt_rest = np.array(m_, float) * [sgn, 1, 1]
        pole = np.array(ik.get('codo_' + side[0], ik.get('codo', (1, -0.5, 0))), float) * [sgn, 1, 1]
        world, idx = mundo(j, rot)
        hips_rest = np.eye(4); hips_rest[:3, 3] = [0, 0.28, 0.009]
        T = (world[idx['Hips']] @ np.linalg.inv(hips_rest) @ np.r_[tgt_rest, 1])[:3]
        ua, la, ha = idx[side + 'UpperArm'], idx[side + 'LowerArm'], idx[side + 'Hand']
        S = world[ua][:3, 3]; l1 = np.linalg.norm(j['nodes'][la]['translation']); l2 = np.linalg.norm(j['nodes'][ha]['translation'])
        d = np.clip(np.linalg.norm(T - S), abs(l1 - l2) + 1e-4, l1 + l2 - 1e-4); dirv = (T - S) / np.linalg.norm(T - S)
        a = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = np.sqrt(max(l1 * l1 - a * a, 0))
        pn = pole - np.dot(pole, dirv) * dirv; pn /= np.linalg.norm(pn) + 1e-12
        E = S + a * dirv + h * pn; T = S + d * dirv
        par = world[idx[side + 'Shoulder']][:3, :3]
        qu = _q_from(np.array(j['nodes'][la]['translation']), par.T @ (E - S)); rot[side + 'UpperArm'] = qu
        par2 = par @ _q_mat(qu)
        rot[side + 'LowerArm'] = _q_from(np.array(j['nodes'][ha]['translation']), par2.T @ (T - E))
    return rot

def posar(j, b, rot):
    """posiciones deformadas de todas las primitivas para un dict {nodo: cuaternión}"""
    idx = {n['name']: i for i, n in enumerate(j['nodes'])}
    local = {i: dict(t=n.get('translation', [0, 0, 0]), r=n.get('rotation', [0, 0, 0, 1]), s=n.get('scale', [1, 1, 1])) for i, n in enumerate(j['nodes'])}
    for nm, q in rot.items(): local[idx[nm]]['r'] = q.tolist()
    world = {}
    def walk(i, P):
        world[i] = P @ render.node_mat({'translation': local[i]['t'], 'rotation': local[i]['r'], 'scale': local[i]['s']})
        for c in j['nodes'][i].get('children', []): walk(c, world[i])
    for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, np.eye(4))
    skin = j['skins'][0]; ibm = render.acc(j, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    JM = np.array([world[ni] @ ibm[k] for k, ni in enumerate(skin['joints'])])
    tris = []
    for p in j['meshes'][0]['primitives']:
        A = p['attributes']; P = render.acc(j, b, A['POSITION']); Jt = render.acc(j, b, A['JOINTS_0']).astype(int); W = render.acc(j, b, A['WEIGHTS_0'])
        P4 = np.c_[P, np.ones(len(P))]; o = np.zeros((len(P), 3))
        for k in range(4): o += W[:, k:k + 1] * np.einsum('nij,nj->ni', JM[Jt[:, k]], P4)[:, :3]
        I = render.acc(j, b, p['indices']).astype(int).reshape(-1, 3)
        pbr = j['materials'][p['material']].get('pbrMetallicRoughness', {})
        tris.append((o[I], render.srgb(np.array(pbr.get('baseColorFactor', [0.8, 0.8, 0.8, 1])[:3])), None, None, None))
    return tris

def escribir_clips(j, binc, poses, dur=0.3):
    """añade un clip por pose (2 llaves: reposo → pose) y devuelve binc extendido"""
    idx = {n['name']: i for i, n in enumerate(j['nodes'])}
    def bv(data):
        while len(binc) % 4: binc.append(0)
        j['bufferViews'].append({'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data)}); binc.extend(data); return len(j['bufferViews']) - 1
    def acc(arr, typ, mn=None, mx=None):
        a = {'bufferView': bv(arr.tobytes()), 'componentType': 5126, 'count': len(arr), 'type': typ}
        if mn is not None: a['min'], a['max'] = mn, mx
        j['accessors'].append(a); return len(j['accessors']) - 1
    t_acc = acc(np.array([0, dur], np.float32), 'SCALAR', [0.0], [dur])
    nombres = {a['name'] for a in j.get('animations', [])}
    for nombre, pose in poses.items():
        if nombre in nombres: j['animations'] = [a for a in j['animations'] if a['name'] != nombre]
        rot = resolver(j, pose); ch, sm = [], []
        for nm, q in rot.items():
            rest = np.array(j['nodes'][idx[nm]].get('rotation', [0, 0, 0, 1]), np.float32)
            sm.append({'input': t_acc, 'output': acc(np.stack([rest, q.astype(np.float32)]), 'VEC4'), 'interpolation': 'LINEAR'})
            ch.append({'sampler': len(sm) - 1, 'target': {'node': idx[nm], 'path': 'rotation'}})
        j.setdefault('animations', []).append({'name': nombre, 'channels': ch, 'samplers': sm})
    return binc

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    raw = open(src, 'rb').read(); Lj = struct.unpack('<I', raw[12:16])[0]
    j = json.loads(raw[20:20 + Lj]); binc = bytearray(raw[28 + Lj:])
    if '--render' in sys.argv:
        from PIL import Image, ImageDraw
        outd = sys.argv[sys.argv.index('--render') + 1]; refs = sys.argv[sys.argv.index('--refs') + 1] if '--refs' in sys.argv else None
        os.makedirs(outd, exist_ok=True)
        laminas = {}
        for nombre, pose in POSES.items(): laminas.setdefault(nombre.split('_')[0], []).append(nombre)
        for lam, nombres in laminas.items():
            W_, H_ = 300, 420; hoja = Image.new('RGB', (W_ * len(nombres), H_ * 2 + 40 if refs else H_), 'white')
            if refs:
                fs = [f for f in os.listdir(refs) if f.startswith(lam[1:] + ' -')]
                if fs:
                    ref = Image.open(os.path.join(refs, fs[0])).convert('RGB'); rw, rh = ref.size
                    # viñetas: 5 columnas entre x≈2 % y 98 %, y≈25 %..77 % (formato de las láminas)
                    x0, x1, y0, y1 = 0.02 * rw, 0.98 * rw, 0.24 * rh, 0.77 * rh; cw = (x1 - x0) / len(nombres)
                    for k in range(len(nombres)):
                        hoja.paste(ref.crop((int(x0 + k * cw), int(y0), int(x0 + (k + 1) * cw), int(y1))).resize((W_, H_)), (W_ * k, 0))
            bnd = (np.array([-0.32, -0.02, -0.32]), np.array([0.32, 0.95, 0.32]))
            for k, nombre in enumerate(nombres):
                tris = posar(j, raw[28 + Lj:], resolver(j, POSES[nombre]))
                im = render.render(tris, 20, W=W_, H=H_, bounds=bnd)
                hoja.paste(im, (W_ * k, H_ + 40 if refs else 0))
                ImageDraw.Draw(hoja).text((W_ * k + 8, (H_ + 12) if refs else 8), nombre, fill=(30, 30, 30))
            hoja.save(os.path.join(outd, f'{lam}.png')); print('hoja', lam)
    binc = escribir_clips(j, binc, POSES)
    j['buffers'] = [{'byteLength': len(binc)}]
    while len(binc) % 4: binc.append(0)
    js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    with open(dst, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc))); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
    print('escrito', dst, len(POSES), 'clips nuevos')
