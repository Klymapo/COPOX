"""Ajusta largos de huesos del esqueleto (Beta) sin tocar las animaciones: escala la traslación local de los huesos
indicados y recalcula las inverseBindMatrices de todo lo que cuelga de ellos (bind pose = pose de reposo, verificado).
Uso: huesos.py in.glb out.glb [UpperArm=0.85] [LowerArm=0.85] [UpperLeg.x=1.2] [Shoulder.z+=0.045] ...   (el nombre se aplica a Left* y Right*)
Nota: escalar 'UpperArm' acorta el brazo superior moviendo a LowerArm; 'LowerArm' acorta el antebrazo moviendo a Hand."""
import json, struct, sys
import numpy as np
sys.path.insert(0, '.')
import render
SRC, OUT = sys.argv[1], sys.argv[2]
fac = {}
for arg in sys.argv[3:]:
    k, v = arg.split('='); fac[k] = float(v)
b = open(SRC, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + L]); binc = bytearray(b[28 + L:])
nodes = j['nodes']; idx = {n['name']: i for i, n in enumerate(nodes)}
hijo = {'UpperArm': 'LowerArm', 'LowerArm': 'Hand', 'UpperLeg': 'LowerLeg', 'LowerLeg': 'Foot'}   # el hueso cuyo largo se escala mueve a este hijo
for k, f in fac.items():
    for side in ('Left', 'Right'):
        if '.' in k:                                     # 'UpperLeg.x=1.2' escala UNA componente de la traslación propia; 'Shoulder.z+=0.04' la desplaza
            nm, comp = k.split('.'); suma = comp.endswith('+'); comp = comp.rstrip('+')
            n = nodes[idx[side + nm]]; t = np.array(n['translation'])
            if suma: t['xyz'.index(comp)] += f
            else: t['xyz'.index(comp)] *= f
            n['translation'] = t.tolist(); print(f'{side}{nm}.{comp}{"+" if suma else "×"}{f}: ahora {t.round(3)}'); continue
        n = nodes[idx[side + hijo[k]]]; t = np.array(n['translation']); n['translation'] = (t * f).tolist()
        print(f'{side}{k}: largo {np.linalg.norm(t)*100:.1f} → {np.linalg.norm(t)*f*100:.1f} cm')
world = {}
def walk(i, P):
    world[i] = P @ render.node_mat(nodes[i])
    for c in nodes[i].get('children', []): walk(c, world[i])
for r in j['scenes'][0]['nodes']: walk(r, np.eye(4))
sk = j['skins'][0]; acc = j['accessors'][sk['inverseBindMatrices']]; bv = j['bufferViews'][acc['bufferView']]
off = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
ibm = np.stack([np.linalg.inv(world[ni]).T for ni in sk['joints']]).astype(np.float32)   # column-major
binc[off:off + ibm.nbytes] = ibm.tobytes()
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js); f.write(struct.pack('<II', len(binc), 0x004E4942)); f.write(binc)
print('escrito', OUT)
