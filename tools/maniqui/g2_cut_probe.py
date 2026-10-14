#!/usr/bin/env python3
"""COPOX G2 · prueba de recorte SOLO en nueva copia GLB, nunca sobre r3.

Aplica máscara protegida derivada de copox.geometry.anatomic_roi; elimina
únicamente triángulos clasificados como candidatos conservadores. NO solda
cabeza y cráneo. Requiere auditoría visual y aprobación antes de usar.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from copox.geometry.anatomic_roi import classify_anatomic_band

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor, write_glb
from g2_anatomic_dryrun import SRC,SHA,boxes,OUT,boundary_edges

DEST=Path("assets/maniqui/maniqui_v0_3_r3_g2_cut_probe.glb")


def build():
    if DEST.exists():
        report_path=OUT/"g2_cut_probe_report.json"
        if not report_path.is_file():
            raise FileExistsError("GLB existente sin reporte de verificación")
        existing=json.loads(report_path.read_text())
        if existing.get("candidate_sha256")!=hashlib.sha256(DEST.read_bytes()).hexdigest() or existing.get("baseline_sha256")!=SHA:
            raise RuntimeError("GLB existente no coincide con el reporte: rechazo")
        print("El mismo candidato verificado ya existe; no se sobrescribe")
        return existing
    if hashlib.sha256(SRC.read_bytes()).hexdigest()!=SHA:
        raise RuntimeError("Baseline no validada")
    j,b=render.load(SRC)
    old=copy.deepcopy(j)
    face,cap=j["meshes"][0]["primitives"][:2]
    fp=render.acc(j,b,face["attributes"]["POSITION"])
    ff=render.acc(j,b,face["indices"]).astype(np.int64).reshape((-1,3))
    cp=render.acc(j,b,cap["attributes"]["POSITION"])
    cf=render.acc(j,b,cap["indices"]).astype(np.int64).reshape((-1,3))
    edges=np.sort(np.vstack([cf[:,[0,1]],cf[:,[1,2]],cf[:,[2,0]]]),axis=1)
    uu,cc=np.unique(edges,axis=0,return_counts=True)
    rim=cp[np.unique(uu[cc==1])]
    roi=classify_anatomic_band(fp,ff,rim,boxes(),
       seam_distance=.015,clearance=.008,angle_center_xz=(-.000038,-.010537))
    if roi.protected.sum()<1 or roi.candidate.sum()<1:
        raise RuntimeError("Sin facciones o sin triángulos para prueba")
    if np.any(roi.protected & roi.candidate):
        raise RuntimeError("Se intentó cortar facción protegida")
    # Auditoría heredada de Codex: protección adicional para TODAS las
    # facciones frontales y orejas, aunque las nuevas cajas no las cubran.
    legacy_features=np.any(((fp[:,2]>.155)&(np.abs(fp[:,0])<.185)&(fp[:,1]<.775))[ff],axis=1)
    legacy_ears=np.any(((np.abs(fp[:,0])>.205)&(fp[:,1]<.712))[ff],axis=1)
    if np.any(roi.candidate & (legacy_features|legacy_ears)):
        raise RuntimeError("CANDIDATO RECHAZADO: recorte viola facciones/orejas de auditoría r3 heredada")
    kept=ff[~roi.candidate]
    kept_set={tuple(x) for x in kept}
    if any(tuple(x) not in kept_set for x in ff[roi.protected]):
        raise RuntimeError("Pérdida de facción protegida")
    after=boundary_edges(kept)
    if after["nonmanifold"]>boundary_edges(ff)["nonmanifold"]:
        raise RuntimeError("Recorte introduce aristas nonmanifold por índice")

    raw=bytearray(b)
    face["indices"]=add_accessor(j,raw,kept.astype(np.uint32).reshape(-1),
                                5125,"SCALAR",34963)
    face.setdefault("extras",{})["g2_probe"]="corte conservador solo sobre caras no protegidas; no soldado"
    j["asset"].setdefault("extras",{})["copox"]="G2 Cut ONLY PROBE, no aprobado ni unido"
    write_glb(DEST,j,raw)
    jj,bb=render.load(DEST)
    if bb[:len(b)]!=b or jj["nodes"]!=old["nodes"] or jj["skins"]!=old["skins"] or jj["animations"]!=old["animations"]:
        raise RuntimeError("Se alteró el rig, las animaciones o los buffers originales")
    for i,p in enumerate(jj["meshes"][0]["primitives"]):
        base=old["meshes"][0]["primitives"][i]
        if i:
            if p!=base:raise RuntimeError("Primitiva fuera de Cara alterada")
        else:
            if p["attributes"]!=base["attributes"]:raise RuntimeError("Atributos de facciones modificados")
    if len(jj["skins"][0]["joints"])!=56 or len(jj["animations"])!=29:
        raise RuntimeError("Conteos de bones/clips distintos")
    if hashlib.sha256(SRC.read_bytes()).hexdigest()!=SHA:raise RuntimeError("Fuente modificada")
    summary={"state":"CUT_ONLY_PROBE_UNAPPROVED","baseline":str(SRC),"baseline_sha256":SHA,
      "output":str(DEST),"candidate_sha256":hashlib.sha256(DEST.read_bytes()).hexdigest(),
      "removed_face_triangles":int(roi.candidate.sum()),
      "protected_face_triangles_preserved":int(roi.protected.sum()),
      "protected_face_triangles_lost":0,
      "face_triangles_after":int(len(kept)),
      "borders_before":boundary_edges(ff),"borders_after":after,
      "buffers_prefix_unmodified":True,"bones":56,"clips":29,
      "unchanged_original_animation_definitions":True,
      "feature_attributes_untouched":True,
      "no_stitch":True,"skull_128_boundary_open":True,
      "not_ready_for_production":True,
      "limitations":["El recorte conserva facciones predefinidas, pero NO limpia toda la isla principal",
       "La transición a la cúpula sigue abierta; no es retopología craneofacial completa",
       "Falta reimportación Godot, pruebas de movimientos continuos, intersecciones y comparación con identidad artística confirmada"]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"g2_cut_probe_report.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=="__main__":build()
