from pathlib import Path
import sys,json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2c4_inspect import BASE
from gltf_sanitize import safe_prepare
import render
root=Path('build/g2c4/godot');root.mkdir(parents=True,exist_ok=True)
models={'V3':BASE,**{k:Path(f'build/g2c4/models/maniqui_G2C4_{k}_SIN_APROBAR.glb') for k in ['A','A2','B','B2','C']}}
for k,p in models.items():
 dest=root/f'{k}_compat.glb'
 if not dest.exists():safe_prepare(str(p),str(dest),str(root/f'{k}_sanitizer.json'))
mask={}
for k in ['A','A2','B','B2','C']:
 report=json.loads(Path(f'docs/maniqui/g2c4/{k}.json').read_text());j,b=render.load(models[k] if k=='C' else BASE);pr=j['meshes'][0]['primitives'][0];v=render.acc(j,b,pr['attributes']['POSITION']);f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3)
 ids=report['affected_retained_triangles'] if k=='C' else report['deleted_triangles']
 mask[k]=v[f[ids]].reshape(-1,3).tolist()
(root/'edited_triangles.json').write_text(json.dumps(mask))
(root/'sources.json').write_text(json.dumps({k:str(v.resolve()) for k,v in models.items()}))

(root/'project.godot').write_text('config_version=5\n[application]\nconfig/name="COPOX G2-C4 QA"\n[display]\nwindow/size/viewport_width=640\nwindow/size/viewport_height=640\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
(root/'qa.gd').write_bytes(Path('tools/maniqui/g2c4_godot.gd').read_bytes())
