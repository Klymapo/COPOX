#!/usr/bin/env python3
"""COPOX · Preparación Stitch real sobre r3 SIN modificar GLB.
Mide distancias entre el borde inferior del cráneo y bordes reales de Cara,
distinguiendo grietas y seams UV. Medición NO es soldadura ni emparejamiento válido.
"""
from __future__ import annotations
import sys,json,hashlib
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render

BASE=Path("assets/maniqui/maniqui_v0_3_r3.glb")
OUT=Path("docs/maniqui/r3_critic_real")
SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"

def border(f):
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]],axis=0),axis=1)
    uniq,count=np.unique(edges,axis=0,return_counts=True)
    return uniq[count==1],int(np.count_nonzero(count>2))

def metrics():
    if hashlib.sha256(BASE.read_bytes()).hexdigest()!=SHA:raise RuntimeError("SHA mismatch")
    j,b=render.load(BASE); parts=j["meshes"][0]["primitives"]
    face,cap=parts[0],parts[1]
    fp=render.acc(j,b,face["attributes"]["POSITION"])
    ff=render.acc(j,b,face["indices"]).astype(np.int64).reshape(-1,3)
    cp=render.acc(j,b,cap["attributes"]["POSITION"])
    cf=render.acc(j,b,cap["indices"]).astype(np.int64).reshape(-1,3)
    cb,nm_cap=border(cf)
    cp_indices=np.unique(cb)
    if len(cb)!=128 or len(cp_indices)!=128 or nm_cap:raise RuntimeError("Cúpula distinta a r3")
    # Solo reconstrucción espacial para análisis, nunca exportar dicha soldadura.
    uniq,inv=np.unique(np.round(fp,6),axis=0,return_inverse=True)
    fb,nm_face=border(inv[ff])
    face_indices=np.unique(fb)
    kd=cKDTree(uniq[face_indices]); distance,near=kd.query(cp[cp_indices],k=1)
    # Clasificar orientación horizontal en 3 zonas a partir de base angular
    center=np.asarray([-.000038,.712,-.010537])
    theta=np.arctan2(cp[cp_indices,2]-center[2],cp[cp_indices,0]-center[0])
    region=np.where(np.sin(theta)>.5,"front",np.where(np.sin(theta)<-.5,"rear","temples"))
    regional={}
    for name in ("front","temples","rear"):
        distances=np.asarray(distance)[region==name]
        regional[name]={"sampled_cap_vertices":int(len(distances)),
            "distance_nearest_face_boundary_mm":{
                "min":round(float(distances.min()*1000),3),
                "median":round(float(np.median(distances)*1000),3),
                "p95":round(float(np.percentile(distances,95)*1000),3),
                "max":round(float(distances.max()*1000),3)},
            "within_5mm":int((distances<=.005).sum()),
            "within_15mm":int((distances<=.015).sum()),
            "within_30mm":int((distances<=.030).sum())}
    # Duplicado de parejas no significa correspondencia 1:1
    selected_face=face_indices[near]
    result={"source":str(BASE),"sha256":SHA,
      "cap_boundary_edges":len(cb),"cap_boundary_vertex_indices":len(cp_indices),
      "face_welded_boundary_edges_1e-6m":len(fb),
      "face_welded_boundary_vertices_1e-6m":len(face_indices),
      "face_welded_nonmanifold_edges":nm_face,
      "nearest_neighbor_face_vertices_unique":int(len(np.unique(selected_face))),
      "nearest_neighbor_collisions":int(len(cp_indices)-len(np.unique(selected_face))),
      "distance_all_mm":{"median":round(float(np.median(distance)*1000),3),
          "p95":round(float(np.percentile(distance,95)*1000),3),
          "maximum":round(float(distance.max()*1000),3)},
      "regional":regional,
      "readiness":{"loop_pair_valid":False,"winding_validated":False,
                   "protected_feature_bridge_safe":False,
                   "stitch_allowed":False,
                   "reason":"La Cara no tiene un loop anatómico equivalente identificado: nearest-neighbor es diagnóstico, no soldadura"},
      "limits":["No transformar materiales UV skin morph ni geometría",
                "El punto más próximo puede ser ceja, oreja, pestaña o isla extra",
                "Antes de Stitch hay que clasificar y aislar un contorno facial, limpiar nonmanifold con máscara anatómica y homologar 128 vértices respetando facciones"]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"stitch_readiness.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"face_boundary_edges":len(fb),"nonmanifold_edges":nm_face,
        "pair_collisions":result["nearest_neighbor_collisions"],
        "mm_by_zone":regional,"stitch_allowed":False},ensure_ascii=False))
    return result
if __name__=="__main__":
    metrics()
