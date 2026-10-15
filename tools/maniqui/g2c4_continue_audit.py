"""Audit exported masters, preserve actual geometry failures, create evidence sheets."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render
from g2c4_inspect import BASE,SHA
from g2c4_intersections import intersections
from g2c4_candidates import topology
root=Path('build/g2c4_continuacion');out=Path('docs/maniqui/g2c4/continuacion_2026-10-15');out.mkdir(parents=True,exist_ok=True)
j,b=render.load(BASE);assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
basegeo=render.gather(BASE)
verdicts={'A3':'RECHAZADO: 31 cruces, pliegues y unión lateral incompleta; no oreja corregida aprobable.','C2':'RECHAZADO: 78 cruces, incluidos 71 con torso; transición anular facetada.','C3':'RECHAZADO: un cruce entre Cabeza 1637 y transición 60; contorno anterior mejora pero la unión sigue facetada/incompleta.'}
for label in ['A3','C2','C3']:
 r=json.loads((root/f'{label}.json').read_text());p=Path(r['glb']);d,raw=render.load(p);assert r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest();assert raw[:len(b)]==b
 for k in ('nodes','skins','animations','materials','images','textures','scenes'):assert d.get(k)==j.get(k),k
 assert d['meshes'][1:]==j['meshes'][1:]
 jp=j['meshes'][0]['primitives'];dp=d['meshes'][0]['primitives']
 if label=='A3':
  assert jp[0]['attributes']==dp[0]['attributes'] and jp[2:]==dp[2:]
  for k,accessor in jp[1]['attributes'].items():
   old=render.acc(j,b,accessor);new=render.acc(d,raw,dp[1]['attributes'][k]);assert np.array_equal(old,new[:len(old)]),k
  oldf=render.acc(j,b,jp[1]['indices']);newf=render.acc(d,raw,dp[1]['indices']);assert np.array_equal(oldf,newf[:len(oldf)])
  assert np.array_equal(render.acc(d,raw,dp[0]['indices']).reshape(-1,3),np.delete(render.acc(j,b,jp[0]['indices']).reshape(-1,3),r['removed_faces'],axis=0))
 else:
  assert jp[1]==dp[1] and jp[3:]==dp[3:]
  assert jp[0]['indices']==dp[0]['indices']
  old=render.acc(j,b,jp[0]['attributes']['POSITION']);new=render.acc(d,raw,dp[0]['attributes']['POSITION']);changed=np.flatnonzero(np.any(old!=new,axis=1));assert set(changed)==set(r['modified_face_vertices'])
  assert np.array_equal(old[:,[0,2]],new[:,[0,2]])
  keep=np.ones(len(old),bool);keep[changed]=False
  for k,a in jp[0]['attributes'].items():
   before=render.acc(j,b,a);after=render.acc(d,raw,dp[0]['attributes'][k]);assert np.array_equal(before[keep],after[keep])
   if k not in ('POSITION','NORMAL'):assert np.array_equal(before,after)
 # Exported bytes, not construction arrays, are the validation source.
 geo=render.gather(p);tris=np.concatenate([g[0] for g in geo]);start=len(geo[0][0])+(len(geo[1][0])-r['added_cap_triangles'] if label=='A3' else len(geo[1][0]))
 changed=np.arange(start,start+(r['added_cap_triangles'] if label=='A3' else len(geo[2][0])))
 if label!='A3':changed=np.r_[r['affected_face_triangles'],changed]
 cross,co=intersections(tris,changed)
 weights=[]
 for pr in dp:
  if 'WEIGHTS_0' in pr['attributes']:
   w=render.acc(d,raw,pr['attributes']['WEIGHTS_0']);joints=render.acc(d,raw,pr['attributes']['JOINTS_0']);assert np.isfinite(w).all() and np.all(w>=0) and np.allclose(w.sum(1),1,atol=2e-5);assert np.all((joints>=0)&(joints<56));weights.append(len(w))
 r.update({'exported_proper_crossings':sorted(cross),'exported_coplanar_aabb_candidates':len(co),'geometry_status':'REJECTED_CROSSINGS' if cross else 'PASS_INITIAL_FILTERS','artistic_status':verdicts[label],'protected_regions_export_audit':'PASS','joint_weight_finiteness_range_and_normalization':'PASS','original_animation_definitions':len(j['animations']),'original_joint_count':len(j['skins'][0]['joints']),'production_approved':False,'intersections_scope':'Changed triangles vs all retained exported geometry at rest; shared-position adjacency excluded; coplanar overlap and continuous poses not certified.'})
 (out/f'{label}.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
 print(label,'invariants PASS; intersections',len(cross))
shutil.copytree(root/'khronos',out/'khronos',dirs_exist_ok=True)
shutil.copy2(root/'godot/godot_report_v3.json',out/'godot_report.json')
report=json.loads((out/'godot_report.json').read_text());assert report['engine']['string'].startswith('4.7.2')
for label,r in report['models'].items():
 assert r['bones']==56 and len(r['clips'])==29 and r['compat_append_error']==0
 assert all(r[k] for k in ['all_bone_samples_match_V3','all_baked_vertices_finite','all_baked_body_samples_match_V3','all_baked_body_normals_match_V3'])
 assert sum(x['tracks']==0 for x in r['clips'])==15
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
cap=root/'godot/captures_v3';sheets=root/'laminas';sheets.mkdir(exist_ok=True)
views=['frontal','perfil_izquierdo','perfil_derecho','posterior','tres_cuartos_izquierdo','tres_cuartos_derecho','posterior_derecho','inferior_mandibula','detalle_oreja_derecha','detalle_ojos','detalle_ojo_izquierdo','detalle_ojo_derecho','detalle_union_cuello']
for label in ['B2','A3','C2','C3']:
 for part,selected in [('cuatro_vistas',views[:4]),('detalles',views[4:]),('poses',[f'pose_{clip}_{view}' for clip in ['Nod','HeadShake','Wave','Sit-pose'] for view in ['frontal','perfil_derecho','posterior']])]:
  canvas=Image.new('RGB',(1024,36+len(selected)*536),'white');draw=ImageDraw.Draw(canvas);draw.text((12,8),f'V3 antes   |   {label} después — Godot 4.7.2 / SIN APROBAR',font=font,fill='black')
  for row,name in enumerate(selected):
   for col,k in enumerate(['V3',label]):
    canvas.paste(Image.open(cap/k/f'{name}.png').resize((512,512)),(col*512,36+row*536));draw.text((col*512+5,36+row*536+513),name,font=font,fill='black')
  canvas.save(sheets/f'{label}_{part}.png')
 canvas=Image.new('RGB',(1280,1320),'white');draw=ImageDraw.Draw(canvas)
 for k,name in enumerate(['frontal','perfil_izquierdo','perfil_derecho','inferior_mandibula']):
  canvas.paste(Image.open(cap/label/f'editados_{name}.png'),((k%2)*640,(k//2)*660));draw.text(((k%2)*640+5,(k//2)*660+640),f'{label} — solo triángulos editados: {name}',font=font,fill='black')
 canvas.save(sheets/f'{label}_solo_editados.png')
images=sorted(cap.rglob('*.png'))+sorted(sheets.glob('*.png'));manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in images}
(out/'CAPTURAS_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
summary={'base_sha256':SHA,'B2_sha256':'daf3737d0cb5b6469fa407ffab5dc761b2fc0e0acd9c69652cb283d41b4b05ec','candidate_decisions':verdicts,'A_iterations_total':3,'B_iterations_total':2,'C_iterations_total':3,'ABC_generated':False,'new_real_Godot_captures':len(list(cap.rglob('*.png'))),'new_sheets':len(list(sheets.glob('*.png'))),'pose_samples':sum(len(v['samples']) for v in report['models'].values()),'production_approved':False}
(out/'RESUMEN.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n');print(summary)
html='<meta charset="utf-8"><title>COPOX G2-C4 continuación</title><style>body{font:18px sans-serif;max-width:1300px;margin:auto}img{max-width:100%}</style><h1>G2-C4 · 15 octubre · SIN APROBAR</h1><p>A3, C2 y C3 rechazados. B2 conservado. Sin ABC. Capturas reales Godot 4.7.2; copias compatibles limitadas, 15 clips faciales vacíos.</p>'
for p in sorted(sheets.glob('*.png')):html+=f'<h2>{p.stem}</h2><a href="laminas/{p.name}"><img loading="lazy" src="laminas/{p.name}"></a>'
(root/'index.html').write_text(html)
