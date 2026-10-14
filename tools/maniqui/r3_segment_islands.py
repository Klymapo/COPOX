#!/usr/bin/env python3
"""COPOX: islas topológicas REALES de Cabeza en r3, con código de colores.

El agrupamiento 1e-6 m es EXCLUSIVAMENTE para diagnóstico: no se sueldan
vértices, ni se cortan triángulos ni se reemplaza el GLB.
"""
from __future__ import annotations
import colorsys
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render

BASE=Path("assets/maniqui/maniqui_v0_3_r3.glb")
OUT=Path("docs/maniqui/r3_critic_real")
SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"

def segment():
    if hashlib.sha256(BASE.read_bytes()).hexdigest()!=SHA:raise RuntimeError("Fuente inesperada")
    j,b=render.load(BASE)
    face=j["meshes"][0]["primitives"][0]
    verts=render.acc(j,b,face["attributes"]["POSITION"])
    triangles=render.acc(j,b,face["indices"]).astype(np.int64).reshape((-1,3))
    # Sólo diagnosticar por posiciones, las primitivas del GLB permanecen iguales.
    spatial,inv=np.unique(np.round(verts,6),axis=0,return_inverse=True)
    F=inv[triangles]
    parent=np.arange(len(spatial))
    def find(i):
        i=int(i)
        while parent[i]!=i:parent[i]=parent[parent[i]];i=int(parent[i])
        return i
    for a,b,c in F:
        root=find(a)
        for other in (b,c):
            q=find(other)
            if root!=q:parent[q]=root
    cluster=defaultdict(list)
    for fi,f in enumerate(F):cluster[find(f[0])].append(fi)
    ordered=sorted(cluster.items(),key=lambda x:-len(x[1]))
    all_roots={r:k for k,(r,indices) in enumerate(ordered)}
    tri_labels=np.array([all_roots[find(f[0])] for f in F],dtype=int)
    areas=np.linalg.norm(np.cross(verts[triangles[:,1]]-verts[triangles[:,0]],
                                   verts[triangles[:,2]]-verts[triangles[:,0]]),axis=1)*.5
    protected=np.any(((verts[:,2]>.155)&(np.abs(verts[:,0])<.185)&(verts[:,1]<.775))[triangles],axis=1)
    ears=np.any(((np.abs(verts[:,0])>.205)&(verts[:,1]<.712))[triangles],axis=1)
    detail=[]
    for label,(root,ids) in enumerate(ordered):
        tr=triangles[np.asarray(ids,dtype=int)]
        points=verts[np.unique(tr)]
        center=points.mean(axis=0)
        detail.append({"island_id":label,"triangles":len(ids),"vertices_raw":len(points),
         "area_m2":round(float(areas[ids].sum()),8),
         "bounds_min":points.min(axis=0).round(6).tolist(),
         "bounds_max":points.max(axis=0).round(6).tolist(),
         "centroid":center.round(6).tolist(),
         "triangles_touching_protected_eye_nose_mouth_mask":int(protected[ids].sum()),
         "triangles_touching_protected_ear_mask":int(ears[ids].sum()),
         "unsafe_to_delete_automatically":True,
         "region_hints_not_anatomical_proof":{
           "front":bool(np.any(points[:,2]>.11)),
           "lateral":bool(np.any(np.abs(points[:,0])>.16)),
           "rear":bool(np.any(points[:,2]<-.08)),
           "low_neck":bool(np.any(points[:,1]<.62))
         }})
    # Colored primitives use actual triangle world positions as read by renderer.
    # The colors indicate connectivity, not goodness or defect.
    tris=render.gather(BASE)
    palette=np.asarray([colorsys.hsv_to_rgb(((i*.61803398875)%1),.72,.86) for i in range(len(ordered))])
    palette=np.asarray([render.srgb(q) for q in palette])
    vc=palette[tri_labels] # one per triangle, not a color per shared vertex
    face_colored=(tris[0][0],np.array([.7,.7,.7]),None,None,vc)
    head=[face_colored,tris[1]]
    hbounds=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
    names=[("Frente",0),("3/4",45),("Perfil",90),("Espalda",180)]
    sheet=Image.new("RGB",(420*4,480+37),(249,249,247));d=ImageDraw.Draw(sheet)
    for i,(name,yaw) in enumerate(names):
        frame=render.render(head,yaw,W=420,H=480,bounds=hbounds)
        sheet.paste(frame,(i*420,37));d.text((i*420+12,8),name+" · islas por conectividad",fill=(30,39,53))
    OUT.mkdir(parents=True,exist_ok=True)
    sheet.save(OUT/"r3_face_islands_4views.png")
    report={"source":str(BASE),"source_sha256":SHA,"weld_tolerance_only_for_diagnosis_m":1e-6,
       "component_count":len(ordered),"components":detail,"method":"numpy.unique rounded positions + union-find by index",
       "colors":"categorical by sorted component triangle count",
       "limitations":["Component != defect: eyes, nose and lips may be separate legitimate islands",
          "Skin/material/UV not modified","Categorical colors are structural, not aesthetic evidence",
          "Segmentation may connect coincident surfaces and miss tiny gaps <1e-6 m"],
       "no_glb_modified":True}
    (OUT/"face_islands.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"components":len(detail),"top_sizes":[x["triangles"] for x in detail[:10]],"protected_islands":[x["island_id"] for x in detail if x["triangles_touching_protected_eye_nose_mouth_mask"] or x["triangles_touching_protected_ear_mask"]]},ensure_ascii=False))
    return report

if __name__=="__main__":
    segment()
