"""Consolida evidencia existente y gates de regresión; no promueve modelos."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from g2c4_inspect import provenance,BASE,SHA
from g2c4_candidates import REPORT,unique_components
j,b,p,f,mp,c,t=provenance();islands=unique_components(p,f);membership=np.zeros(len(f),int)
for i,faces in enumerate(islands):membership[faces]=i
engine=json.loads(Path('build/g2c4/godot/godot_report_v3.json').read_text())
kh=json.loads((REPORT/'khronos/summary.json').read_text());statuses={
 'A':('REJECTED_ARTISTIC','El recorte de 156 caras de pelo deja un hueco visible detrás de la oreja.'),
 'A2':('REJECTED_ARTISTIC','El recorte limitado de 63 caras conserva saliente y deja hueco; no repetir por inercia.'),
 'B':('PARTIAL_SUPERSEDED','61 caras de montura retiradas; sobreviven diez residuos confirmados.'),
 'B2':('REGIONAL_CLEANUP_REVIEWABLE_GLOBAL_BLOCKED','71 caras confirmadas de montura retiradas. Ojos y facciones retenidos; huecos faciales históricos no reparados. No certificación de expresiones funcionales.'),
 'C':('REJECTED_ANATOMICAL','Contorno menos dentado, pero aplanado y sin transición ni anillo de cuello reutilizable. La mejora numérica no satisface anatomía/topología.')}
summary={'baseline_sha256':SHA,'baseline_pr':46,'baseline_immutable':hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA,'models':{},'ABC_generated':False,'reason_no_ABC':'A/A2 y C no pasan sus criterios; todos los maestros mantienen bloqueo glTF heredado. B2 se conserva independientemente.','approval':False,'merge':False,'paid_tools':False}
for label,(state,why) in statuses.items():
 path=REPORT/f'{label}.json';r=json.loads(path.read_text());r['artistic_status']=state;r['artistic_reason']=why;r['global_acceptance']=False
 ids=np.array(r['deleted_triangles'],dtype=int)
 r['deleted_baseline_islands']=np.unique(membership[ids]).tolist();r['exact_reference_triangles']=mp[ids].tolist()
 r['new_intersections']='NONE_IN_TESTED_REGION_REST_POSE; see C_intersections.json' if label=='C' else r['new_intersections']
 g=engine['models'][label]
 assert r['original_binary_prefix_exact'] and r['cranium_nape_all_other_primitives_exact']
 assert r['new_degenerate_faces_count']==0 and not r['new_inverted_faces']
 assert g['bones']==56 and len(g['clips'])==29 and g['all_bone_samples_match_V3'] and g['all_baked_vertices_finite']
 assert g['all_baked_body_samples_match_V3'] and g['all_baked_body_normals_match_V3']
 assert kh[label]['master']['errors']==kh['V3']['master']['errors']
 r['godot']={k:g[k] for k in ['raw_append_error','compat_append_error','bones','surfaces','blend_shape_count','all_bone_samples_match_V3','all_baked_vertices_finite','all_baked_body_samples_match_V3','all_baked_body_normals_match_V3','baked_vertex_samples']}
 path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 summary['models'][label]={'sha256':r['sha256'],'deleted':r['deleted_count'],'moved':r['modified_vertex_count'],'status':state,'reason':why,'regression_checks_pass':True,'global_pass':False}
(REPORT/'RESUMEN.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# Actual anatomical frame: no invented neck aperture written to the model.
world={}
import render
def walk(i,P):
 world[i]=P@render.node_mat(j['nodes'][i])
 for child in j['nodes'][i].get('children',[]):walk(child,world[i])
for root in j['scenes'][j.get('scene',0)]['nodes']:walk(root,np.eye(4))
neck=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='Neck');head=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='Head');axis=world[head][:3,3]-world[neck][:3,3];axis/=np.linalg.norm(axis)
C=json.loads((REPORT/'C.json').read_text());v=p[C['modified_vertices']]
neck_primitive=j['meshes'][0]['primitives'][2];neck_points=render.acc(j,b,neck_primitive['attributes']['POSITION'])
neckreport={'units':'m','up':'Y','front':'+Z','neck_joint_world':world[neck][:3,3].tolist(),'head_joint_world':world[head][:3,3].tolist(),'neck_head_axis':axis.tolist(),'edited_jaw_min':v.min(0).tolist(),'edited_jaw_max':v.max(0).tolist(),'boundary_spatial_samples':np.unique(np.round(v,6),axis=0).tolist(),'existing_neck_primitive_bounds':[neck_points.min(0).tolist(),neck_points.max(0).tolist()],'proposed_anchor_for_future_study':world[head][:3,3].tolist(),'proposed_section_normal_for_future_study':axis.tolist(),'actual_connection_ring_created':False,'connection_topology_status':'NONE_VALIDATED; branched historical boundaries, no closed annulus','neck_ready':False,'reason':'A smoothing-only jaw does not make an animatable attachment. Existing neck width 0.3415 m and open head base need a separate controlled reconstruction. No arbitrary cap or ring was added.'}
(REPORT/'CUELLO_ANATOMIA.json').write_text(json.dumps(neckreport,indent=2)+'\n')
godotout=REPORT/'godot';godotout.mkdir(exist_ok=True)
for name in ['godot_report_v3.json','qa_v3.log',*[f'{k}_sanitizer.json' for k in ['V3','A','A2','B','B2','C']]]:shutil.copy2(Path('build/g2c4/godot')/name,godotout/name)
files=[*Path('build/g2c4/godot/captures_v3').rglob('*.png'),*Path('build/g2c4/laminas_finales').glob('*.png')]
(REPORT/'CAPTURAS_SHA256.json').write_text(json.dumps({str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(files)},indent=2)+'\n')
shutil.copy2('build/g2c4/regional_tests.log',REPORT/'regional_tests.log')
print(json.dumps(summary,ensure_ascii=False))
