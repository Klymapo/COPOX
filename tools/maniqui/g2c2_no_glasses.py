#!/usr/bin/env python3
"""Real r3 + wardrobe: remove only explicitly named Lentes primitive.

Generate true 4-view before/after evidence, a derived wardrobe GLB and
a JSON audit. Source files are SHA-checked and NEVER overwritten.
Unlabeled residues on skin remain a separate manual-review blocker.
"""
from __future__ import annotations
import hashlib
import json
import sys
import copy
import tempfile
from pathlib import Path

from PIL import Image,ImageDraw
import numpy as np

from copox.geometry.eyewear_guard import eyewear_gate,remove_labeled_eyewear

sys.path.insert(0,str(Path("tools/maniqui").resolve()))
import render
from reparar_v03 import write_glb

HEAD=Path("assets/maniqui/maniqui_v0_3_r3.glb")
WARDROBE=Path("assets/maniqui/ropa_alastor_v0.glb")
SHA_HEAD="3aec25dd8c9f758bc7b092806caf159efb073be71bbba6615c2905c692f6dd0b"
OUT_DIR=Path("docs/maniqui/g2c2")
OUT_GL=Path("assets/maniqui/ropa_alastor_g2c2_sin_lentes.glb")
VIEWS=[("FRONTAL",0),("3/4",45),("PERFIL",90),("POSTERIOR",180)]
BOUNDS=(np.array([-.29,.51,-.29]),np.array([.29,1.,.29]))


def hashfile(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def is_geom(p):
    return p.get("mode",4)==4


def make_evidence():
    if hashfile(HEAD)!=SHA_HEAD:
        raise RuntimeError("Baseline r3 inesperada; no tocar nada")
    if not WARDROBE.is_file() or OUT_GL.exists():
        raise RuntimeError("Wardrobe inexistente o candidato ya creado: no sobrescribir")

    head_doc,head_bin=render.load(HEAD)
    cloth_doc,cloth_bin=render.load(WARDROBE)
    original_wardrobe_sha=hashfile(WARDROBE)

    inventory=eyewear_gate(head_doc,cloth_doc)
    if inventory["source_face_explicit_eyewear_primitives"]:
        raise RuntimeError("Hay lentes etiquetados dentro del maniquí; requerir auditoría adicional")
    clean,removed=remove_labeled_eyewear(cloth_doc,expected_count=1)
    if len(clean["meshes"])!=len(cloth_doc["meshes"]):
        raise RuntimeError("No cambiar estructura de meshes")
    if (clean.get("nodes")!=cloth_doc.get("nodes")
        or clean.get("skins")!=cloth_doc.get("skins")
        or clean.get("animations")!=cloth_doc.get("animations")
        or clean.get("materials")!=cloth_doc.get("materials")):
        raise RuntimeError("Invariante glTF dañada")

    # Keep original data and its buffer verbatim; only the reference to
    # the eyewear primitive is omitted in the new, unapproved clothing GLB.
    write_glb(OUT_GL,clean,bytearray(cloth_bin))
    chk,bin_out=render.load(OUT_GL)
    if bin_out!=cloth_bin or chk["skins"]!=cloth_doc["skins"] or chk["animations"]!=cloth_doc["animations"]:
        raise RuntimeError("Rig/animations/binary buffer changed")
    if any(x.get("extras",{}).get("pieza")=="Lentes" for mesh in chk["meshes"]
           for x in mesh.get("primitives",[])):
        raise RuntimeError("Lentes remained")
    if hashfile(WARDROBE)!=original_wardrobe_sha or hashfile(HEAD)!=SHA_HEAD:
        raise RuntimeError("A source was modified")

    # Real glass primitive before removal; show 4 views of the same head
    # and identical camera in each row.
    # Render the *exact* named piece from a temporary view-only GLB.
    # The source may include multiple meshes/nodes and primitive indexing in
    # render.gather() isn't guaranteed to correspond to meshes[0].primitives.
    with tempfile.TemporaryDirectory(prefix="copox_glasses_") as tmp:
        accessory=copy.deepcopy(cloth_doc)
        matches={(entry["mesh"],entry["primitive"]) for entry in removed}
        for mi,mesh in enumerate(accessory["meshes"]):
            mesh["primitives"]=[
                p for pi,p in enumerate(mesh.get("primitives",[]))
                if (mi,pi) in matches
            ]
        glass_only=Path(tmp)/"view_only_glasses.glb"
        write_glb(glass_only,accessory,bytearray(cloth_bin))
        glasses=[part for part in render.gather(glass_only) if len(part[0])]
        if not glasses:
            raise RuntimeError("No visible glasses triangles found in separately labeled source")
    head_tris=render.gather(HEAD)[:2]
    before=head_tris+glasses
    after=head_tris
    image=Image.new("RGB",(4*400,2*(440+34)),(248,249,250))
    label=ImageDraw.Draw(image)
    for row,(status,geometry) in enumerate(
        [("ANTES · CON LENTES",before),("DESPUES · SIN LENTES",after)]):
        for col,(view,yaw) in enumerate(VIEWS):
            frame=render.render(geometry,yaw,W=400,H=440,bounds=BOUNDS)
            y0=row*(440+34)
            image.paste(frame,(col*400,y0+34))
            label.text((col*400+8,y0+9),f"{status} | {view}",fill=(28,38,50))
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    image.save(OUT_DIR/"G2C2_LENTES_4V_COMPARATIVA.png")

    audit={
      "head_source":str(HEAD),"head_sha256":SHA_HEAD,
      "wardrobe_source":str(WARDROBE),"wardrobe_sha256":original_wardrobe_sha,
      "candidate_wardrobe":str(OUT_GL),"candidate_sha256":hashfile(OUT_GL),
      "removed_primitive_names":["Lentes"],
      "removed_primitive_count":len(removed),
      "removed_primitive_details":removed,
      "glasses_removed_only_from_separately_labeled_accessory":True,
      "historical_head_geometry_untouched":True,
      "wardrobe_buffers_unchanged":True,
      "wardrobe_skin_and_animations_equal":True,
      "face_eye_eyebrow_ear_triangles_untouched":True,
      "all_four_views_compared_same_camera":True,
      "visual_comparison":"docs/maniqui/g2c2/G2C2_LENTES_4V_COMPARATIVA.png",
      "eyewear_goal":"no frame, no lenses, no bridge and no temple arms",
      "risk":"Labeled accessories removed, but embedded unlabeled frame remnants inside face geometry are not yet ruled out",
      "unlabeled_eyewear_residue_multiview_audit":"PENDING",
      "anatomic_contour_for_stitch":"PENDING",
      "artistic_approval":False,
      "source_models_modified":False,
      "candidate_production_ready":False,
      "stage":"EYWEAR_ACCESSORY_REMOVED__FACE_RESIDUE_REVIEW_REQUIRED",
      "notes":"After preview re-renders r3 head plus glasses-only triangles from historical wardrobe, not an artistic approval or stitched head"
    }
    (OUT_DIR/"EYWEAR_GUARD.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in audit.items() if k not in ("removed_primitive_details",)},ensure_ascii=False))
    return audit


if __name__=="__main__":
    make_evidence()
