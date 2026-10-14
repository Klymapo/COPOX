"""COPOX G2-C2 · Eyewear Guardian: remover accesorios etiquetados, no ojos.

Conserva la escena, esqueleto, accesores, materiales y animaciones en una
COPIA. Sólo elimina primitivas inequívocamente etiquetadas como gafas/lentes.
Si los anteojos comparten triángulos con la Cara, BLOCKED para revisión.
"""
from __future__ import annotations
import copy
import re
from dataclasses import dataclass

# Word boundaries prevent accidentally deleting "eye"/"eyes"/"eyelid" or
# materials named "LensFlare" used outside eyewear accessories.
_EYEWEAR = re.compile(r"(?i)(?:^|[\s_\-.])(?:lentes|gafas|anteojos|glasses|eyewear|spectacles)(?:$|[\s_\-.])")


def _strings(value):
    if isinstance(value,str):
        return [value]
    if isinstance(value,dict):
        result=[]
        for key,v in value.items():
            if key in ("pieza","part","part_name","name","asset_type","category") and isinstance(v,str):
                result.append(v)
        return result
    return []


def find_labeled_eyewear(gltf):
    """Return exactly identified primitive positions, no guessed geometry."""
    found=[]
    meshes=gltf.get("meshes",[])
    mats=gltf.get("materials",[])
    for mi,mesh in enumerate(meshes):
        for pi,prim in enumerate(mesh.get("primitives",[])):
            labels=_strings(prim.get("extras"))
            labels+=_strings(prim.get("name"))
            # Material names are supporting metadata only: never enough on
            # their own, since a source may share one material across face.
            own=any(_EYEWEAR.search(s) for s in labels)
            material=prim.get("material")
            material_name=mats[material].get("name","") if isinstance(material,int) and 0<=material<len(mats) else ""
            if own:
                found.append({"mesh":mi,"primitive":pi,
                              "piece_label":labels,
                              "material_name":material_name,
                              "source":"explicit_primitive_identity"})
    return found


def remove_labeled_eyewear(gltf, *, expected_count=None):
    """Return a new JSON glTF tree. No binary changes or index remaps.

    The caller exports to a different GLB path. A skinned mesh with
    remaining face / mouth / eyes remains untouched, even if its material
    is shared with an eyeglass part.
    """
    records=find_labeled_eyewear(gltf)
    if expected_count is not None and len(records)!=expected_count:
        raise ValueError(f"Expected {expected_count} eyewear primitives, found {len(records)}")
    out=copy.deepcopy(gltf)
    selected={(x["mesh"],x["primitive"]) for x in records}
    for mi,mesh in enumerate(out.get("meshes",[])):
        mesh["primitives"]=[prim for pi,prim in enumerate(mesh.get("primitives",[]))
                            if (mi,pi) not in selected]
    if find_labeled_eyewear(out):
        raise RuntimeError("Eyewear remained after filtering")
    return out,records


def eyewear_gate(face_gltf,wardrobe_gltf):
    """Named pieces are objective evidence; facial residue needs art review."""
    on_head=find_labeled_eyewear(face_gltf)
    on_wardrobe=find_labeled_eyewear(wardrobe_gltf)
    return {"source_face_explicit_eyewear_primitives":on_head,
            "source_wardrobe_explicit_eyewear_primitives":on_wardrobe,
            "target_should_include_eyewear":False,
            "target_face_landmarks_protected":["eyes","eyelids","eyebrows","nose","ears","temples"],
            "label_removal_is_not_residue_detection":True,
            "possible_unlabeled_frame_fragments_require_multiview_review":True,
            "eyewear_removal_allowed_only_if_separately_labeled":True,
            "face_geometry_must_not_be_deleted_for_eyewear":True,
            "all_source_models_preserved":True,
            "production_visual_approval":False}


def classify_possible_embedded_eyewear(face_vertices, face_triangles,
                                      accessory_vertices, protected_faces,
                                      *, search_radius_m=0.006):
    """Only TRIAGE remnants near removed frames; returns no deletion mask.

    Eye contours frequently lie near eyeglass frames. A proximity search
    cannot distinguish eyelids from unlabeled frame polygons. Protection wins.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    p=np.asarray(face_vertices,dtype=float)
    f=np.asarray(face_triangles,dtype=np.int64)
    accessory=np.asarray(accessory_vertices,dtype=float)
    protected=np.asarray(protected_faces)
    if (p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all()
        or f.ndim!=2 or f.shape[1]!=3 or len(f)==0
        or f.min()<0 or f.max()>=len(p)):
        raise ValueError("Geometría facial inválida")
    if (accessory.ndim!=2 or accessory.shape[1]!=3 or len(accessory)==0
        or not np.isfinite(accessory).all()):
        raise ValueError("Puntos de lentes originales inválidos")
    if protected.dtype!=bool or protected.shape!=(len(f),):
        raise ValueError("Protección de triángulos obligatoria")
    if not np.isfinite(search_radius_m) or search_radius_m<=0:
        raise ValueError("Radio inválido")
    distances,_=cKDTree(accessory).query(p[f].mean(axis=1),k=1,workers=1)
    near=distances<=search_radius_m
    return {
        "distances_m":distances,
        "near_protected":near&protected,
        "near_unprotected_for_review":near&~protected,
        "far":~near,
        "remove_allowed":False,
        "method":"KDTree distance to separately extracted eyewear vertex points; TRIAGE ONLY",
        "warning":"Proximity is not eyewear identity; no facial triangles may be removed without multi-view proof",
    }
