#!/usr/bin/env python3
"""COPOX G2-C2-R · cassette experimental para NUCA, independiente del rostro.

Exports GLB sibling preserving ALL old primitive data and original buffer as
an unchanged prefix. This operation does not promise a fully closed neck.
Reports a region verdict that is NOT vetoed by unrelated facial defects.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

from copox.geometry.partial_nape import rear_nape_patch
from copox.geometry.regional_review import RegionVerdict,aggregate_regional_review

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import add_accessor,write_glb

SRC=Path("assets/maniqui/maniqui_v0_3_r3.glb")
EXPECTED="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
CAND=Path("assets/maniqui/maniqui_v0_3_r3_nuca_local_prototipo.glb")
EVIDENCE=Path("docs/maniqui/g2c2/nuca")


def make(profile="flat"):
    if profile not in ("flat","eased"):
        raise ValueError("Perfil de nuca desconocido")
    CAND=(Path("assets/maniqui/maniqui_v0_3_r3_nuca_local_suavizada.glb")
          if profile=="eased" else Path("assets/maniqui/maniqui_v0_3_r3_nuca_local_prototipo.glb"))
    EVIDENCE=(Path("docs/maniqui/g2c2/nuca/suavizada") if profile=="eased"
              else Path("docs/maniqui/g2c2/nuca"))
    if not SRC.is_file() or hashlib.sha256(SRC.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError("Baseline original no verificado")
    if CAND.exists():
        raise FileExistsError("Se prohíbe reemplazar candidatos")
    j,b=render.load(SRC)
    original=copy.deepcopy(j)
    if len(j.get("skins",[]))!=1 or len(j["skins"][0]["joints"])!=56 or len(j["animations"])!=29:
        raise RuntimeError("Rig original no coincide")
    prims=j["meshes"][0]["primitives"]
    if prims[0].get("extras",{}).get("pieza")!="Cabeza" or prims[1].get("extras",{}).get("pieza")!="Craneo":
        raise RuntimeError("Esperadas Cabeza y Craneo")
    cap=prims[1]
    if "targets" in cap:
        raise RuntimeError("Morph targets de cráneo no soportados: bloquear")
    attrs={key:render.acc(j,b,index) for key,index in cap["attributes"].items()}
    expected_keys={"POSITION","NORMAL","JOINTS_0","WEIGHTS_0"}
    if set(attrs)!=expected_keys:
        raise RuntimeError("Atributos extra no previstos: no descartarlos")
    f=render.acc(j,b,cap["indices"]).astype(np.int64).reshape((-1,3))
    patch=rear_nape_patch(attrs["POSITION"],f,drop_m=.042,radial_scale=.970,
                          rear_z_max=-.083,lateral_x_max=.175,min_edges=8,
                          profile=profile)
    # Ancestry is the exact original rim source for the new vertices.
    newattrs={}
    for key,data in attrs.items():
        if key=="POSITION":
            val=patch.positions
        elif key=="NORMAL":
            val=np.concatenate((data,data[patch.ancestry]),axis=0)
        else:
            val=np.concatenate((data,data[patch.ancestry]),axis=0)
        newattrs[key]=val
    if np.max(np.abs(newattrs["WEIGHTS_0"].sum(axis=1)-1))>1e-5:
        raise RuntimeError("Joint weights invalid")
    if np.any(newattrs["JOINTS_0"]>=56):
        raise RuntimeError("Unsupported joint index")
    raw=bytearray(b)
    for key,data in newattrs.items():
        old=original["accessors"][cap["attributes"][key]]
        ct=int(old["componentType"]);ty=old["type"]
        cap["attributes"][key]=add_accessor(j,raw,np.asarray(data,dtype=render.CT[ct]),
                                              ct,ty,34962,key=="POSITION")
    cap["indices"]=add_accessor(j,raw,patch.faces.astype(np.uint32).reshape(-1),
                                  5125,"SCALAR",34963)
    cap.setdefault("extras",{})["copox_region"]="NUCA ONLY - partial open patch; unapproved"
    j["asset"].setdefault("extras",{})["copox"]="G2C2 NUCA candidate; facial defects evaluated separately"
    write_glb(CAND,j,raw)

    verify,buf=render.load(CAND)
    if (buf[:len(b)]!=b or verify["animations"]!=original["animations"] or
        verify["skins"]!=original["skins"] or
        verify["nodes"]!=original["nodes"] or
        verify["materials"]!=original["materials"]):
        raise RuntimeError("Rig/animation/material/buffer original altered")
    if verify["meshes"][0]["primitives"][0]!=original["meshes"][0]["primitives"][0]:
        raise RuntimeError("La CARA cambió pese a ser una región congelada")
    if verify["meshes"][0]["primitives"][2:]!=original["meshes"][0]["primitives"][2:]:
        raise RuntimeError("Algunas otras piezas del cuerpo cambiaron")
    exported=verify["meshes"][0]["primitives"][1]
    newv=render.acc(verify,buf,exported["attributes"]["POSITION"])
    newf=render.acc(verify,buf,exported["indices"]).astype(np.int64).reshape((-1,3))
    if not np.array_equal(newv[:len(attrs["POSITION"])],attrs["POSITION"]):
        raise RuntimeError("Cambio en vertices originales del cráneo")
    if not np.array_equal(newf[:len(f)],f):
        raise RuntimeError("Cambio en caras originales del cráneo")
    if np.any(newv[len(attrs["POSITION"]):,2]>=-.083):
        raise RuntimeError("La nueva nuca invade parte frontal")
    if hashlib.sha256(SRC.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError("Fuente original modificada")

    # Four standardized cameras, same geometry sources and framing.
    views=[("FRENTE",0),("PERFIL",90),("NUCA",180),("NUCA 3/4",225)]
    bounds=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))
    base=render.gather(SRC)[:2]
    candidate=render.gather(CAND)[:2]
    canvas=Image.new("RGB",(4*390,2*468),"white")
    draw=ImageDraw.Draw(canvas)
    for row,(label,tris) in enumerate((("r3 ORIGINAL",base),("NUCA LOCAL",candidate))):
        for col,(view,angle) in enumerate(views):
            frame=render.render(tris,angle,W=390,H=438,bounds=bounds)
            canvas.paste(frame,(col*390,row*468+30))
            draw.text((col*390+10,row*468+7),label+(" "+profile.upper() if profile!="flat" else "")+" | "+view,fill=(25,38,52))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    canvas.save(EVIDENCE/"NUCA_LOCAL_ANTES_DESPUES_4V.png")
    # Truthful visual QA: highlight ONLY triangles appended at the back.
    # All colored faces originate from the reimported candidate GLB.
    old_face_count=len(f)
    if candidate[1][0].shape[0]!=old_face_count+len(patch.new_faces):
        raise RuntimeError("Face count changed during rendered GLB reimport")
    patch_tri=candidate[1][0][old_face_count:]
    highlighted=(patch_tri,np.array([.08,.55,.86]),None,None,None)
    older_cap=(candidate[1][0][:old_face_count],candidate[1][1],None,None,None)
    marked=Image.new("RGB",(4*390,468),"white")
    ink=ImageDraw.Draw(marked)
    for col,(view,angle) in enumerate(views):
        frame=render.render([candidate[0],older_cap,highlighted],angle,
                            W=390,H=438,bounds=bounds)
        marked.paste(frame,(col*390,30))
        ink.text((col*390+10,7),view+" | NUEVOS TRIANGULOS AZULES",fill=(25,38,52))
    marked.save(EVIDENCE/"NUCA_SOLO_TRIANGULOS_NUEVOS_4V.png")
    # A region can pass structural validation despite face being left unresolved.
    report=aggregate_regional_review({
       "nuca":RegionVerdict("nuca","PASS","REVIEW_REQUIRED",True,True),
       "cara":RegionVerdict("cara","UNTESTED","REVIEW_REQUIRED",True,True,
                           ("Cara congelada; conservar r3 sin limpieza todavía",)),
       "orejas":RegionVerdict("orejas","UNTESTED","REVIEW_REQUIRED",True,True),
       "manos":RegionVerdict("manos","UNTESTED","REVIEW_REQUIRED",True,True),
       "vestuario":RegionVerdict("vestuario","UNTESTED","REVIEW_REQUIRED",True,True),
       "piernas":RegionVerdict("piernas","UNTESTED","REVIEW_REQUIRED",True,True),
       "rig_y_animaciones":RegionVerdict("rig_y_animaciones","PASS","REVIEW_REQUIRED",True,True),
    },target_region="nuca")
    result={
       "source":str(SRC),"source_sha256":EXPECTED,
       "derived_glb":str(CAND),"profile":profile,
       "derived_sha256":hashlib.sha256(CAND.read_bytes()).hexdigest(),
       "bones":56,"animation_definitions":29,
       "face_unchanged":True,"rest_of_body_unchanged":True,
       "material_defs_unchanged":True,"original_binary_buffer_unchanged":True,
       "new_rear_only":True,
       "glb_reimport_structural_check_passed":True,
       "local_patch_metrics":patch.report,
       "regional_review":report,
       "comparison":"docs/maniqui/g2c2/nuca/NUCA_LOCAL_ANTES_DESPUES_4V.png",
       "patch_highlight":"docs/maniqui/g2c2/nuca/NUCA_SOLO_TRIANGULOS_NUEVOS_4V.png",
       "status":"NUCA_LOCAL_TECHNICAL_PASS__VISUAL_REVIEW_REQUIRED",
       "warning":"Es un parche parcial ABIERTO, no una cabeza soldada ni aprobación estética",
       "not_auto_promoted":True,
       "no_baseline_overwrite":True,
    }
    (EVIDENCE/"REPORTE_NUCA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"metrics":patch.report,
                      "glb":str(CAND)},ensure_ascii=False))
    return result

if __name__=="__main__":
    make()
