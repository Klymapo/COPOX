#!/usr/bin/env python3
"""G2-C2 · buscar restos de montura sin confundirlos con facciones.

NO eliminar geometría: proximidad a lentes históricos NO prueba que los
triángulos cercanos sean vidrio/montura. Mostrar evidencia en 4 vistas.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw
from copox.geometry.eyewear_guard import classify_possible_embedded_eyewear

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from g2_anatomic_dryrun import boxes

HEAD=Path("assets/maniqui/maniqui_v0_3_r3.glb")
GLASSES=Path("assets/maniqui/ropa_alastor_v0.glb")
HEAD_SHA="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT=Path("docs/maniqui/g2c2")


def protected_by_boxes(positions,faces):
    corners=positions[faces]
    protect=np.zeros(len(faces),dtype=bool)
    hits={}
    for region in boxes():
        lo=np.array(region.minimum)
        hi=np.array(region.maximum)
        hit=np.any(np.all((corners>=lo)&(corners<=hi),axis=2),axis=1)
        protect|=hit
        hits[region.name]=int(hit.sum())
    legacy=np.any(((positions[:,2]>.155)&(abs(positions[:,0])<.185)&
                   (positions[:,1]<.775))[faces],axis=1)
    ears=np.any(((abs(positions[:,0])>.205)&(positions[:,1]<.712))[faces],axis=1)
    protect|=legacy|ears
    return protect,{**hits,"legacy_features":int(legacy.sum()),"legacy_ears":int(ears.sum())}


def run():
    if hashlib.sha256(HEAD.read_bytes()).hexdigest()!=HEAD_SHA:
        raise RuntimeError("r3 baseline cambiada")
    hj,hb=render.load(HEAD)
    wj,wb=render.load(GLASSES)
    face=hj["meshes"][0]["primitives"][0]
    fp=render.acc(hj,hb,face["attributes"]["POSITION"])
    ff=render.acc(hj,hb,face["indices"]).astype(int).reshape(-1,3)
    selections=[(mi,pi,p)
       for mi,m in enumerate(wj["meshes"])
       for pi,p in enumerate(m["primitives"])
       if p.get("extras",{}).get("pieza")=="Lentes"]
    if len(selections)!=1:raise RuntimeError("Sin fuente única etiquetada Lentes")
    mi,pi,p=selections[0]
    glass=render.acc(wj,wb,p["attributes"]["POSITION"])
    frozen,per_box=protected_by_boxes(fp,ff)

    scans={}
    colors=None
    for mm in (3,6,10):
        r=classify_possible_embedded_eyewear(fp,ff,glass,frozen,search_radius_m=mm/1000)
        scans[str(mm)]={"distance_threshold_mm":mm,
           "near_protected_faces":int(r["near_protected"].sum()),
           "near_unprotected_faces_for_review":int(r["near_unprotected_for_review"].sum()),
           "far_faces":int(r["far"].sum()),
           "near_unprotected_face_indices":np.flatnonzero(r["near_unprotected_for_review"]).tolist(),
           "near_protected_face_indices":np.flatnonzero(r["near_protected"]).tolist(),
           "face_triangles_deleted":0}
        if mm==6:colors=r
    # Emphasize potential residues in scarlet and protected anatomy in teal:
    # this is a diagnostic color map, not proof that the red polys are glasses.
    original=render.gather(HEAD)
    if not original or len(original[0][0])!=len(ff):
        raise RuntimeError("Triangle order from renderer doesn't match indexed face mesh")
    face_rgb=np.array([[.61,.65,.68]]*len(ff))
    face_rgb[colors["near_protected"]]=[.21,.68,.71]
    face_rgb[colors["near_unprotected_for_review"]]=[.89,.29,.29]
    face_color=render.srgb(face_rgb)
    face_prim=(original[0][0],np.array([.6,.6,.6]),None,None,face_color)
    head=[face_prim,original[1]]
    names=[("FRENTE",0),("3/4",45),("PERFIL",90),("ESPALDA",180)]
    canvas=Image.new("RGB",(4*400,470),(250,249,247))
    draw=ImageDraw.Draw(canvas)
    bounds=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
    for i,(label,yaw) in enumerate(names):
        frame=render.render(head,yaw,W=400,H=440,bounds=bounds)
        canvas.paste(frame,(400*i,30))
        draw.text((400*i+12,10),f"{label}: restos potenciales (ROJO)",fill=(23,38,54))
    OUT.mkdir(parents=True,exist_ok=True)
    canvas.save(OUT/"G2C2_RESIDUOS_LENTES_4V.png")
    report={
      "head_sha256":HEAD_SHA,
      "eyewear_source_sha256":hashlib.sha256(GLASSES.read_bytes()).hexdigest(),
      "glasses_piece":{"mesh":mi,"primitive":pi,"vertices":len(glass)},
      "original_face_triangles":len(ff),
      "protected_triangles":int(frozen.sum()),
      "protection_regions_overlapping_counts":per_box,
      "radius_reports":scans,
      "visual_sheet":"docs/maniqui/g2c2/G2C2_RESIDUOS_LENTES_4V.png",
      "color_legend":{"red":"near lens piece and unprotected: investigate, not removal",
                      "turquoise":"near lens piece but frozen facial anatomy",
                      "gray":"other face triangles"},
      "assessment":"REVIEW_REQUIRED",
      "presumed_eyewear_triangle_deletion_allowed":False,
      "triangles_deleted":0,
      "original_head_sha256_after":hashlib.sha256(HEAD.read_bytes()).hexdigest(),
      "warnings":[
         "Proximity to the removed frame does not prove residual eyewear",
         "Eye, eyebrow and ear geometry remains protected",
         "No shape change, no stitch, no glasses-residue clearance claim",
         "Render uses rest-pose views; artistic reference set still incomplete"
      ],
    }
    (OUT/"G2C2_RESIDUE_REPORT.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("radius_reports","protection_regions_overlapping_counts")},ensure_ascii=False))
    print("counts",[(key,s["near_unprotected_faces_for_review"],s["near_protected_faces"]) for key,s in scans.items()])
    return report

if __name__=="__main__":
    run()
