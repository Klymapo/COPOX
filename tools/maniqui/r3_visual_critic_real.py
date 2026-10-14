#!/usr/bin/env python3
"""Primer ensayo sobre el Maniquí r3 REAL: comparar todas las referencias 3D identificadas.

No modifica el GLB ni inventa semejanza con diseños incompatibles. Baseline SHA.
Entrada pública: refs/* previamente versionadas en COPOX. Sin descargas ni APIs.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw
from copox.visual.critic import audit
from copox.visual.geometry_planner import propose

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render

BASE=Path("assets/maniqui/maniqui_v0_3_r3.glb")
EXPECTED="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT=Path("docs/maniqui/r3_critic_real")
RELEVANT=[
 ("detective_portrait","refs/personajes/detective.jpg","three_quarter",
  "Detective de pelo castaño/gafas: identidad respecto a r3 requiere confirmación"),
 ("alastor_pending","refs/pendientes/alastor-1790548802009.jpg","three_quarter",
  "Referencia etiquetada Alastor; duplicado visual probable de detective.jpg"),
 ("older_male","refs/personajes/hombre-mayor.png","three_quarter",
  "Hombre mayor canoso y barba: alternativa o personaje distinto sin confirmación"),
 ("pair_older_male","refs/personajes/joven-rubio-y-hombre-mayor.png","three_quarter",
  "Contexto de hombre mayor con Theo: NO referencia frontal/ortográfica"),
 ("turnaround_sheet","refs/infografias/hoja-de-vistas-personaje.png","reference_sheet",
  "Lámina multivista de personaje: sus vistas internas deben segmentarse e identificarse"),
 ("character_comparison","refs/infografias/comparativa-visual-de-personajes.png","reference_sheet",
  "Comparativa gráfica multicaracter; no mezclar sujetos y escalas"),
]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def edges_and_components(vertices,indices,*,round_decimals=None):
    faces=np.asarray(indices,dtype=np.int64)
    points=np.asarray(vertices,dtype=float)
    if round_decimals is not None:
        positions,inv=np.unique(np.round(points,decimals=round_decimals),axis=0,return_inverse=True)
        faces=inv[faces]
    else:
        positions=points
    ed=np.sort(np.vstack((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1)
    _,ct=np.unique(ed,axis=0,return_counts=True)
    # Components from vertex connectivity. Index seams won't be mistaken for
    # physical gaps when round_decimals is supplied (diagnostic only).
    parent=np.arange(len(positions),dtype=np.int64)
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=int(parent[i])
        return i
    for i,j in ed:
        a=find(int(i));b=find(int(j))
        if a!=b:parent[b]=a
    populated=np.unique(faces)
    roots=Counter(find(int(i)) for i in populated)
    return {"positions":int(len(positions)),"components":int(len(roots)),
      "largest_component_vertices":sorted(roots.values(),reverse=True)[:10],
      "open_boundary_edges":int(np.count_nonzero(ct==1)),
      "nonmanifold_edges":int(np.count_nonzero(ct>2)),
      "degenerate_triangles":int(np.sum((faces[:,0]==faces[:,1])|(faces[:,1]==faces[:,2])|(faces[:,0]==faces[:,2])))}

def analyze():
    OUT.mkdir(parents=True,exist_ok=True)
    if digest(BASE)!=EXPECTED:raise RuntimeError("Fuente r3 distinta: abortar")
    j,b=render.load(BASE)
    if len(j.get("skins",[]))!=1 or len(j["skins"][0]["joints"])!=56 or len(j["animations"])!=29:
        raise RuntimeError("Rig o clips distintos; abortar")
    p=j["meshes"][0]["primitives"]
    if p[0].get("extras",{}).get("pieza")!="Cabeza" or p[1].get("extras",{}).get("pieza")!="Craneo":
        raise RuntimeError("Orden de primitivas inesperado")
    out={"source":str(BASE),"sha256":EXPECTED,
       "bones":len(j["skins"][0]["joints"]),"clips":len(j["animations"]),
       "coordinate_contract":{"up":"Y","front":"+Z","unit":"meters"},
       "primitives":[],"conclusions":[]}
    for i in (0,1):
        prim=p[i]
        xyz=render.acc(j,b,prim["attributes"]["POSITION"])
        faces=render.acc(j,b,prim["indices"]).astype(int).reshape(-1,3)
        raw=edges_and_components(xyz,faces)
        quantized=edges_and_components(xyz,faces,round_decimals=6)
        out["primitives"].append({"part":prim["extras"]["pieza"],
            "vertices":len(xyz),"triangles":len(faces),"raw_by_index":raw,
            "position_weld_for_diagnosis_only_1e-6":quantized,
            "bounds_min":xyz.min(axis=0).round(7).tolist(),
            "bounds_max":xyz.max(axis=0).round(7).tolist(),
            "warnings":["Algunos cortes por UV producen bordes por índice, no agujeros",
                        "Agrupar por posición es SÓLO diagnóstico; no exportar soldadura así"]})
    cap=out["primitives"][1]
    out["cap_boundary_edges_indexed"]=cap["raw_by_index"]["open_boundary_edges"]
    out["conclusions"]=[
        "El borde de cúpula abierto por índice no significa que estén soldadas sus piezas con la Cara",
        "R3 conserva 56 bones y 29 clips; inspección de malla NO certifica comportamiento de animación",
        "Las referencias originales tienen identidad/ropa/focal distintas y no son métricas calibradas de la esfera calva",
        "No medir semejanza artística por IoU con referencias de cámara desconocida",
        "No cortar patillas ni nuca sin máscaras de protección validadas contra todas las referencias"
    ]
    (OUT/"topologia_r3.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    return out

def visual_and_manifest(topology):
    tris=render.gather(BASE)
    full=np.concatenate([x[0].reshape(-1,3) for x in tris])
    bounds=(full.min(axis=0),full.max(axis=0))
    views=[("front",0),("three_quarter",45),("side",90),("back",180)]
    views_out=[]
    contact=Image.new("RGB",(440*4,550+44),"white")
    d=ImageDraw.Draw(contact)
    for index,(name,yaw) in enumerate(views):
        im=render.render(tris,yaw,W=440,H=550,bounds=bounds)
        path=OUT/f"r3_{name}.png";im.save(path)
        views_out.append({"view":name,"pose":"rest","image":str(path)})
        contact.paste(im,(index*440,44));d.text((index*440+12,10),name.upper(),fill=(30,39,52))
    (OUT/"r3_fourviews.png").parent.mkdir(parents=True,exist_ok=True)
    contact.save(OUT/"r3_fourviews.png")
    # Head only: the SAME source GLB and cameras, not generated concept art.
    hbounds=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
    head=Image.new("RGB",(420*4,480+36),"white");draw=ImageDraw.Draw(head)
    for index,(name,yaw) in enumerate(views):
        frame=render.render(tris[:2],yaw,W=420,H=480,bounds=hbounds)
        head.paste(frame,(index*420,36));draw.text((index*420+12,8),name,fill=(30,39,52))
    head.save(OUT/"r3_head_details.png")
    views_out.append({"view":"reference_sheet","pose":"rest","image":str(OUT/"r3_fourviews.png")})
    refs=[];supplied=[]
    for rid,path,view,note in RELEVANT:
        if not Path(path).is_file():raise FileNotFoundError(path)
        refs.append({"id":rid,"image":path,"view":view,"pose":"rest",
            "camera_alignment":"unknown",
            "reference_role":"contextual_uncalibrated",
            "notes":note})
        supplied.append(path)
    manifest={"asset_id":"maniqui_v0_3_r3","required_views":[v for v,_ in views],
        "provided_reference_files":supplied,"references":refs,
        "candidate":{"id":"r3_original_unmodified","views":views_out},
        "anomalies":[{"id":"r3_cap_open_boundary","region":"skull_face_transition",
            "description":"Cúpula y Cara son primitivas diferentes; cúpula con bordes abiertos por índice",
            "per_reference":{r["id"]:{"assessment":"uncertain",
                 "note":"Referencia sin cámara calibrada y sin render anatómico equivalente; no concluir error artístico de esta imagen"}
                 for r in refs}}]}
    (OUT/"references_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    # Validates 6 physically existing references, comparing every image individually.
    # A scene/turnaround image is marked as context, not as proof of likeness.
    review=audit(manifest,root=Path("."),output=OUT/"visual_review",make_sheets=True)
    t=topology["primitives"][1]["raw_by_index"]
    diag={"anomalies":{"r3_cap_open_boundary":{
        "kind":"open_seam","target_boundary_edges":t["open_boundary_edges"],
        "loop_vertex_counts":None,
        "loop_winding_valid":False,"attributes_compatible":False,
        "morph_targets_present":None,"max_gap_m":None,
        "measurement_provenance":{"source_sha256":EXPECTED,
            "measurement_method":"render.acc indexed GLB triangle edges; no UV weld",
            "coordinate_system":"Y-up meters front+Z"}}}}
    (OUT/"mesh_measurements.json").write_text(json.dumps(diag,ensure_ascii=False,indent=2)+"\n")
    plan=propose(review,diag)
    (OUT/"geometry_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
    summary={"state":"AUDITED_NOT_MODIFIED",
        "model_sha256":EXPECTED,"references_found":len(refs),
        "refs_compared":review["references_compared"],
        "all_references_accounted_for_in_this_repo_selection":review["all_references_accounted_for"],
        "visual_status":review["status"],"operator_plan_status":plan["status"],
        "plan_recommendations":plan["recommendations"],
        "open_cap_edges_by_index":t["open_boundary_edges"],
        "no_mutated_model":True,"no_artistic_approval":True,
        "not_proven_complete_user_reference_history":True,
        "warning":"No hay cámara exacta ni referencias 3D de la cabeza calva; se requiere segmentar la hoja multivista, confirmar identidad y máscaras anatómicas antes de cortar o soldar."}
    (OUT/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="plan_recommendations"},ensure_ascii=False))
    return summary

if __name__=="__main__":
    topology=analyze()
    summary=visual_and_manifest(topology)
    if summary["refs_compared"]!=len(RELEVANT) or not summary["no_mutated_model"]:
        raise SystemExit("La cobertura o protección falló")
