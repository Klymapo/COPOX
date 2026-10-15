"""Isolated QA for continuation: never overwrite the initial campaign."""
from pathlib import Path
import sys,json,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render
from g2c4_inspect import BASE
from gltf_sanitize import safe_prepare
root=Path('build/g2c4_continuacion/godot');root.mkdir(parents=True,exist_ok=True)
models={'V3':BASE,'B2':Path('build/g2c4/models/maniqui_G2C4_B2_SIN_APROBAR.glb')}
for k in ['A3','C2','C3']:models[k]=Path(json.loads(Path(f'build/g2c4_continuacion/{k}.json').read_text())['glb'])
for k,p in models.items():
 dest=root/f'{k}_compat.glb'
 if not dest.exists():safe_prepare(str(p),str(dest),str(root/f'{k}_sanitizer.json'))
j,b=render.load(BASE);pr=j['meshes'][0]['primitives'][0];p=render.acc(j,b,pr['attributes']['POSITION']);f=render.acc(j,b,pr['indices']).astype(int).reshape(-1,3)
mask={}
for k in ['B2','A3']:
 r=json.loads(Path(f'docs/maniqui/g2c4/{k}.json' if k=='B2' else f'build/g2c4_continuacion/{k}.json').read_text());ids=r['deleted_triangles'] if k=='B2' else r['removed_faces'];v=p[f[ids]].reshape(-1,3)
 if k=='A3':
  patch=np.load('build/g2c4_continuacion/A3_patch.npz');v=np.vstack([v,patch['positions'][patch['faces']].reshape(-1,3)])
 mask[k]=v.tolist()
for k in ['C2','C3']:
 patch=np.load(f'build/g2c4_continuacion/{k}_patch.npz');mask[k]=np.vstack([patch['changed_positions'],patch['positions'][patch['faces']].reshape(-1,3)]).tolist()
(root/'edited_triangles.json').write_text(json.dumps(mask));(root/'sources.json').write_text(json.dumps({k:str(v.resolve()) for k,v in models.items()}))
(root/'project.godot').write_text('config_version=5\n[application]\nconfig/name="COPOX G2-C4 continuación"\n[display]\nwindow/size/viewport_width=640\nwindow/size/viewport_height=640\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
s=Path('tools/maniqui/g2c4_godot.gd').read_text().replace('["V3","A","A2","B","B2","C"]','["V3","B2","A3","C2","C3"]').replace('surface>=2','surface>=3')
s=s.replace('"no artistic approval implied"','"no artistic approval implied", "body invariants cover surfaces >=3; surface 2 is the authorized jaw/neck transition in C2/C3", "A3 and C2 rendered for rejection evidence after failing initial geometry filters"')
(root/'qa.gd').write_text(s)
# Keep validator reports separate from the initial immutable campaign.
v=Path('tools/maniqui/g2c4_validate.cjs').read_text().replace('build/g2c4/godot','build/g2c4_continuacion/godot').replace('docs/maniqui/g2c4/khronos','build/g2c4_continuacion/khronos');(root/'validate.cjs').write_text(v)
