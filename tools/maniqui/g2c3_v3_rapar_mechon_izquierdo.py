#!/usr/bin/env python3
"""COPOX G2-C3 V3 · rapado MINIMO del mechon suelto detras de oreja izquierda.

Edita el GLB V2 COMPLETO (sha de origen obligatorio), NO la calva, ni la
geometria de la oreja. Unicamente elimina indices de los 8 triangulos de
una isla TOPOLÓGICAMENTE DESCONECTADA en la zona posterior izquierda.
La V2 se reconstruye bit a bit desde r3 si el artefacto no esta presente.
El codigo falla cerrado si la isla desaparece o cambia de identidad.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageChops
from copox.geometry.kernel import GeometryError
from tools.maniqui import g2c3_surface_rebuild_v2 as v2

sys.path.insert(0, str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor, write_glb

SOURCE=Path("assets/maniqui/maniqui_v0_3_r3_g2c3_nuca_completo_v2_SIN_APROBAR.glb")
SOURCE_SHA="b7998d382f13ef8997a2dc2f73539a61da9ec5aa27605897534b13d47f3517e6"
RESULT=Path("assets/maniqui/maniqui_v0_3_r3_g2c3_v3_rapado_oreja_izquierda_SIN_APROBAR.glb")
EVIDENCE=Path("docs/maniqui/g2c3/oreja_izquierda_v3")
BOUNDS=(np.array([-.29,.51,-.29]),np.array([.29,1.0,.29]))
VIEWS=(("FRENTE",0),("3/4 FRONTAL IZQ",45),("PERFIL IZQ",90),
       ("3/4 POSTERIOR IZQ",135),("NUCA",180),("PERFIL DERECHO",270))
DETAIL_VIEWS=(("PERFIL IZQ",70),("PERFIL EXACTO",90),
              ("3/4 POSTERIOR IZQ",125),("NUCA IZQ",145))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reconstruct_exact_source_if_needed():
    """Genera desde el cassette aprobado SOLO COMO BASE, nunca lo sustituye."""
    if not SOURCE.exists():
        base,binary=render.load(v2.SRC)
        info=v2.write_candidate("completo_v2",v2.PROFILES["completo_v2"],base,binary)
        if info["glb"]!=str(SOURCE):
            raise RuntimeError("Ruta V2 reconstruida distinta")
    if sha(SOURCE)!=SOURCE_SHA:
        raise RuntimeError("V2 de origen no coincide con SHA256: NO CORTAR")
    return SOURCE

def unique_components(positions,faces):
    """Contigüidad por coordenadas redondeadas solo para diagnóstico.
    No soldar, ni cambiar indices/vértices del GLB.
    """
    p=np.asarray(positions)
    f=np.asarray(faces,dtype=np.int64)
    spatial,vertex_spatial=np.unique(np.round(p,6),axis=0,return_inverse=True)
    welded_faces=vertex_spatial[f]
    parent=np.arange(len(spatial))
    def root(i):
        i=int(i)
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=int(parent[i])
        return i
    for tri in welded_faces:
        r=root(tri[0])
        for idx in tri[1:]:
            v=root(idx)
            if r!=v:
                parent[v]=r
                r=root(r)
    parts={}
    for fi,tri in enumerate(welded_faces):
        parts.setdefault(root(tri[0]),[]).append(fi)
    return [np.asarray(v,dtype=np.int64) for v in parts.values()]

def identify_tuft(positions,faces):
    """Aísla ÚNICAMENTE las ocho caras reales del mechón tras oreja izquierda.
    Ancla anatómica r3 registrada antes de este paso:
    X [-.222786,-.199735], Y [.703391,.734685], Z [-.131243,-.105095].
    La isla principal de orejas/cara cuenta miles de caras: está blindada.
    """
    islands=unique_components(positions,faces)
    matches=[]
    for indices in islands:
        if len(indices)!=8:
            continue
        pts=positions[np.unique(faces[indices].reshape(-1))]
        low=pts.min(axis=0)
        high=pts.max(axis=0)
        target_low=np.array([-.222786,.703391,-.131243])
        target_high=np.array([-.199735,.734685,-.105095])
        if (np.all(np.abs(low-target_low)<.00004) and
            np.all(np.abs(high-target_high)<.00004)):
            matches.append((indices,low,high))
    if len(matches)!=1:
        sizes=sorted((len(x) for x in islands if len(x)<50),reverse=True)
        raise GeometryError(
            "El pelo lateral aislado de 8 caras no es unico: NO EDITAR. "
            f"Coincidencias {len(matches)}, islas pequenas {sizes}")
    ids,low,high=matches[0]
    # Every triangle sits BEHIND and OUTSIDE the left ear attachment.
    pts=positions[faces[ids]]
    if (np.any(pts[:,:,0]>=-.198) or np.any(pts[:,:,2]>=-.100)
        or np.any(pts[:,:,1]<=.699) or np.any(pts[:,:,1]>=.739)):
        raise GeometryError("El recorte invade posible pabellon/rostro")
    # Connectivity checks: none of the deleted triangles shares one vertex
    # or same rounded coordinate with any retained face.
    others=np.delete(faces,ids,axis=0)
    gone=np.unique(faces[ids]); keep=np.unique(others)
    if len(np.intersect1d(gone,keep)):
        raise GeometryError("No es una isla: indices compartidos con oreja")
    rounded_removed={tuple(v) for v in np.round(positions[gone],6)}
    if any(tuple(v) in rounded_removed for v in np.round(positions[keep],6)):
        raise GeometryError("No es isla aislada geométricamente: proteccion")
    return ids,low,high,{"component_count":len(islands),
                         "removed_faces":len(ids),"removed_face_ids":ids.tolist(),
                         "bounds_min":low.round(6).tolist(),
                         "bounds_max":high.round(6).tolist(),
                         "all_adjacent_ear_faces_preserved":True}

def create_v3():
    if RESULT.exists():
        raise FileExistsError("No sobrescribir GLB V3 existente")
    reconstruct_exact_source_if_needed()
    srcdoc,srcbin=render.load(SOURCE)
    orig=copy.deepcopy(srcdoc)
    doc=copy.deepcopy(srcdoc)
    origpr=orig["meshes"][0]["primitives"]
    pr=doc["meshes"][0]["primitives"]
    if (origpr[0].get("extras",{}).get("pieza")!="Cabeza"
        or origpr[1].get("extras",{}).get("pieza")!="Craneo"
        or len(orig.get("skins",[]))!=1
        or len(orig["skins"][0]["joints"])!=56
        or len(orig["animations"])!=29):
        raise RuntimeError("No es el maniquí V2 aprobado como fuente")
    pos=render.acc(orig,srcbin,origpr[0]["attributes"]["POSITION"])
    before=render.acc(orig,srcbin,origpr[0]["indices"]).astype(np.int64).reshape(-1,3)
    ids,lo,hi,details=identify_tuft(pos,before)
    after=np.delete(before,ids,axis=0)
    raw=bytearray(srcbin)
    doc["meshes"][0]["primitives"][0]["indices"]=add_accessor(
        doc,raw,after.astype(np.uint32).reshape(-1),5125,"SCALAR",34963)
    doc["meshes"][0]["primitives"][0].setdefault("extras",{})[
        "copox_v3_left_ear_tuft"]="8 detached hair faces omitted; ear untouched"
    doc["asset"].setdefault("extras",{})["copox_v3"]="UNAPPROVED local ear-tuft shave"
    write_glb(RESULT,doc,raw)
    j,b=render.load(RESULT)
    newpr=j["meshes"][0]["primitives"]
    if (b[:len(srcbin)]!=srcbin or
        any(j.get(k)!=orig.get(k) for k in
            ("skins","animations","nodes","materials","scenes","textures","images")) or
        newpr[1:]!=origpr[1:] or
        newpr[0]["attributes"]!=origpr[0]["attributes"] or
        newpr[0].get("targets")!=origpr[0].get("targets") or
        newpr[0].get("material")!=origpr[0].get("material")):
        raise RuntimeError("Se modificó algo fuera de los índices del mechón")
    reloaded=render.acc(j,b,newpr[0]["indices"]).astype(np.int64).reshape(-1,3)
    if not np.array_equal(reloaded,after):
        raise RuntimeError("GLB reimportado no tiene las caras previstas")
    if sha(SOURCE)!=SOURCE_SHA:
        raise RuntimeError("Fuente V2 fue alterada")
    details.update({"source_sha256":SOURCE_SHA,"candidate_sha256":sha(RESULT),
        "old_face_count":len(before),"new_face_count":len(after),
        "unchanged_original_buffer_prefix":True,
        "skull_cap_unchanged":True,
        "face_ear_vertices_unchanged":True,
        "facial_morph_targets_unchanged":True,
        "ear_nearby_triangles_unchanged":True,
        "bone_count":56,"animation_definitions":29,
        "model_glb":str(RESULT),"artistic_approval":False})
    return details

def pixel_measure(a,b):
    diff=np.max(np.abs(np.asarray(a).astype(int)-
                       np.asarray(b).astype(int)),axis=2)
    return int(np.count_nonzero(diff>=6))

def projected_at(centroid,angle,w,h,bounds):
    ang=math.radians(angle)
    rot=np.array([[math.cos(ang),0,math.sin(ang)],
                  [0,1,0],[-math.sin(ang),0,math.cos(ang)]])
    ctr=(bounds[0]+bounds[1])/2
    ext=bounds[1]-bounds[0]
    scale=.92*min(w/max(ext[0],ext[2]),h/ext[1])
    pt=(centroid-ctr)@rot.T
    return int(pt[0]*scale+w/2),int(-pt[1]*scale+h/2)

def render_evidence(details):
    source=render.gather(SOURCE)[:2]
    candidate=render.gather(RESULT)[:2]
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    comparison=Image.new("RGB",(6*400,2*455),"white")
    draw=ImageDraw.Draw(comparison)
    deltas={}
    for col,(name,angle) in enumerate(VIEWS):
        old=render.render(source,angle,W=400,H=430,bounds=BOUNDS)
        new=render.render(candidate,angle,W=400,H=430,bounds=BOUNDS)
        comparison.paste(old,(400*col,25))
        comparison.paste(new,(400*col,480))
        draw.text((400*col+9,8),"V2 ORIG | "+name,fill=(16,30,43))
        draw.text((400*col+9,462),"V3 RASURADA | "+name,fill=(16,30,43))
        deltas[name]=pixel_measure(old,new)
    comp=EVIDENCE/"V2_V3_ANTES_DESPUES_6V.png"
    comparison.save(comp)

    # True pixel zoom on anatomical ear zone in four camera angles:
    center=np.array([-.211,.72,-.117])
    close=Image.new("RGB",(4*540,2*595),"white")
    pen=ImageDraw.Draw(close)
    close_counts={}
    for col,(name,angle) in enumerate(DETAIL_VIEWS):
        W=720;H=720
        old=render.render(source,angle,W=W,H=H,bounds=BOUNDS)
        new=render.render(candidate,angle,W=W,H=H,bounds=BOUNDS)
        x,y=projected_at(center,angle,W,H,BOUNDS)
        region=(x-135,y-135,x+135,y+135)
        a=old.crop(region).resize((540,540),Image.Resampling.NEAREST)
        b=new.crop(region).resize((540,540),Image.Resampling.NEAREST)
        close.paste(a,(col*540,27))
        close.paste(b,(col*540,622))
        pen.text((col*540+8,9),"V2 | "+name,fill=(16,30,43))
        pen.text((col*540+8,604),"V3 | "+name,fill=(16,30,43))
        close_counts[name]=pixel_measure(a,b)
    zoom=EVIDENCE/"OREJA_IZQUIERDA_CLOSEUP_ANTES_DESPUES.png"
    close.save(zoom)
    details["pixels_changed_by_view"]=deltas
    details["zoom_pixels_changed_by_view"]=close_counts
    details["visual_change_detected"]=max(close_counts.values())>4
    details["evidence_six_views"]=str(comp)
    details["evidence_ear_zoom"]=str(zoom)
    # Distinguish actually hidden fragments from visible. Fail closed rather
    # than claiming a visual repair that did not show up in any view.
    if not details["visual_change_detected"]:
        raise GeometryError("Mechón retirado pero ninguna diferencia perceptible: revisar ROI")
    return details

def run():
    details=create_v3()
    details=render_evidence(details)
    report={
      "status":"LEFT_EAR_ISOLATED_TUFT_REMOVED__TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED",
      "baseline":"G2-C3 V2 completo (no re-esculpir casco)",
      "source_glb":str(SOURCE),
      "derived_glb":str(RESULT),
      "technical":details,
      "limitations":[
        "La seguridad protege oreja/cara por conectividad REAL de 8 triángulos",
        "No prueba animaciones faciales en movimiento ni cierra cabeza/cara",
        "La aprobación artística requiere revisar dos zooms reales",
        "GLB V2 r3 original y fuentes no se sustituyen ni se fusionan"],
      "no_merge":True,"no_original_replacement":True}
    (EVIDENCE/"REPORTE_V3.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"mesh":str(RESULT),
      "sha":details["candidate_sha256"],"removed_faces":details["removed_faces"],
      "diffs":details["zoom_pixels_changed_by_view"]},ensure_ascii=False))
    return report

if __name__=="__main__":
    run()
