from pathlib import Path
import sys,json,numpy as np
import os
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gltf_sanitize import safe_prepare
from g2c4_inspect import BASE
import render
labels=sys.argv[1:] or ['R1'];root=Path(os.environ.get('G2C5_QA_ROOT','build/g2c5/godot_'+'_'.join(labels)));root.mkdir(parents=True,exist_ok=True)
models={'V3':BASE,'B2':Path('build/g2c4/models/maniqui_G2C4_B2_SIN_APROBAR.glb')}
for k in labels:models[k]=Path(json.loads(Path(f'docs/maniqui/g2c5/{k}.json').read_text())['glb'])
for k,p in models.items():
 dest=root/f'{k}_compat.glb'
 if not dest.exists():safe_prepare(str(p),str(dest),str(root/f'{k}_sanitizer.json'))
j,b=render.load(BASE);pr=j['meshes'][0]['primitives'][0];p=render.acc(j,b,pr['attributes']['POSITION']);f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3);ids=json.loads(Path('docs/maniqui/g2c4/B2.json').read_text())['deleted_triangles'];masks={'B2':p[f[ids]].reshape(-1,3).tolist()}
for k in labels:masks[k]=np.load(f'build/g2c5/{k}_edit.npz')['triangles'].reshape(-1,3).tolist()
(root/'edited_triangles.json').write_text(json.dumps(masks));(root/'sources.json').write_text(json.dumps({k:str(p.resolve()) for k,p in models.items()}))
(root/'project.godot').write_text('config_version=5\n[application]\nconfig/name="COPOX G2-C5 QA"\n[display]\nwindow/size/viewport_width=640\nwindow/size/viewport_height=640\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
s=Path('tools/maniqui/g2c4_godot.gd').read_text()
# Keep the label list in lockstep with sources.json; the C4 script's historic
# candidate list otherwise silently skips every G2-C5 model during captures.
s=s.replace('for label in ["V3","A","A2","B","B2","C"]:',
            'for label in '+json.dumps(list(models))+':')
s=s.replace('func _initialize():','func _initialize():\n    views.append(["detalle_nariz_frontal",0.0,0.0,Vector3(0,.664,.20),.18])\n    views.append(["detalle_nariz_perfil",270.0,0.0,Vector3(0,.664,.20),.18])\n    views.append(["detalle_nariz_tres_cuartos",315.0,0.0,Vector3(0,.664,.20),.18])')
(root/'qa.gd').write_text(s)
v=Path('tools/maniqui/g2c4_validate.cjs').read_text().replace('build/g2c4/godot',str(root)).replace('docs/maniqui/g2c4/khronos',str(root/'khronos'));(root/'validate.cjs').write_text(v)
print('QA root',root)
