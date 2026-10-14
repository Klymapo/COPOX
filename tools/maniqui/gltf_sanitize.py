"""COPOX: saneamiento glTF estricto para importadores que rechazan accessors vacíos.

NO retopología, NO cambia vértices originales, NO inventa rig ni clips.
Sólo elimina primitivas realmente vacías y accesores no utilizables COUNT=0
cuando ninguna referencia estructural válida depende de ellos.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import render
from reparar_v03 import write_glb


def safe_prepare(source: str, target: str, report_path: str) -> dict:
    src=Path(source); dest=Path(target)
    if not src.is_file() or dest.exists():
        raise RuntimeError("GLB inexistente o destino ya existe; no sobrescribir")
    j,b=render.load(src)
    original=copy.deepcopy(j)
    m=j.get("meshes",[])
    accessors=j.get("accessors",[])
    dropped_primitive=[]
    valid_meshes=[]
    mesh_remap={}
    for mi,mesh in enumerate(m):
        remaining=[]
        for pi,prim in enumerate(mesh.get("primitives",[])):
            attr=prim.get("attributes",{})
            pos_idx=attr.get("POSITION")
            if pos_idx is None or pos_idx<0 or pos_idx>=len(accessors):
                raise ValueError(f"Mesh {mi} primitive {pi} sin POSITION válido")
            position_count=accessors[pos_idx].get("count",-1)
            indices_id=prim.get("indices")
            indices_count=accessors[indices_id].get("count",-1) if indices_id is not None else position_count
            if position_count==0 or indices_count==0:
                dropped_primitive.append({"mesh":mi,"primitive":pi,
                    "position_count":position_count,"indices_count":indices_count,
                    "material":prim.get("material")})
                continue
            if position_count<0 or indices_count<0:
                raise RuntimeError("Accessor count inválido no vacío")
            remaining.append(prim)
        if remaining:
            mesh["primitives"]=remaining
            mesh_remap[mi]=len(valid_meshes)
            valid_meshes.append(mesh)
    j["meshes"]=valid_meshes
    removed_meshes=sorted(set(range(len(m)))-set(mesh_remap))
    for node in j.get("nodes",[]):
        if "mesh" in node:
            old=node["mesh"]
            if old in mesh_remap:
                node["mesh"]=mesh_remap[old]
            else:
                node.pop("mesh")
                node.pop("skin",None)
    # Collect only glTF core accessor references after pruning EMPTY primitives.
    uses=[]
    for mesh in j.get("meshes",[]):
        for prim in mesh["primitives"]:
            for name,k in prim.get("attributes",{}).items():
                uses.append((k,f"mesh attr {name}"))
            if "indices" in prim:uses.append((prim["indices"],"mesh indices"))
            for target_i,target in enumerate(prim.get("targets",[])):
                for name,k in target.items():uses.append((k,f"morph {target_i}:{name}"))
    for i,skin in enumerate(j.get("skins",[])):
        if "inverseBindMatrices" in skin:
            uses.append((skin["inverseBindMatrices"],f"skin {i} matrices"))
    for ai,anim in enumerate(j.get("animations",[])):
        for si,sampler in enumerate(anim.get("samplers",[])):
            uses.extend([(sampler["input"],f"animation {ai}.{si} input"),
                         (sampler["output"],f"animation {ai}.{si} output")])
    for idx,why in uses:
        if not isinstance(idx,int) or idx<0 or idx>=len(accessors):
            raise RuntimeError("Referencia de accessor fuera de rango: "+str((idx,why)))
        if accessors[idx].get("count",0)<=0:
            raise RuntimeError(f"Accessor VACÍO aún referenciado, rechazo: {idx} ({why})")
    zeros=[k for k,a in enumerate(accessors) if a.get("count")==0]
    keep=[i for i,a in enumerate(accessors) if a.get("count")!=0]
    amap={old:new for new,old in enumerate(keep)}
    def remap():
        for mesh in j.get("meshes",[]):
            for prim in mesh["primitives"]:
                prim["attributes"]={name:amap[k] for name,k in prim["attributes"].items()}
                if "indices" in prim:prim["indices"]=amap[prim["indices"]]
                if "targets" in prim:
                    prim["targets"]=[{name:amap[k] for name,k in target.items()} for target in prim["targets"]]
        for skin in j.get("skins",[]):
            if "inverseBindMatrices" in skin:
                skin["inverseBindMatrices"]=amap[skin["inverseBindMatrices"]]
        for anim in j.get("animations",[]):
            for sampler in anim.get("samplers",[]):
                sampler["input"]=amap[sampler["input"]]
                sampler["output"]=amap[sampler["output"]]
    remap()
    j["accessors"]=[accessors[i] for i in keep]
    if len(j.get("skins",[]))!=len(original.get("skins",[])) or len(j["animations"])!=len(original["animations"]):
        raise RuntimeError("No preservar clips/skin invalida saneamiento")
    if len(dropped_primitive)==0 and len(zeros)==0:
        status="NOOP_SOURCE_ALREADY_VALID"
    else: status="SAFE_EMPTY_DATA_REMOVED"
    write_glb(dest,j,bytearray(b))
    dj,db=render.load(dest)
    if db!=b or len(dj["animations"])!=len(original["animations"]):
        raise RuntimeError("Binary or animation metadata mutated")
    for skin in dj["skins"]:
        if len(skin.get("joints",[]))!=56:
            raise RuntimeError("Skeleton joint count changed")
    result={"source":str(src),"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
        "sanitized":str(dest),"sanitized_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
        "state":status,"zero_count_accessors_removed":len(zeros),
        "zero_count_accessor_ids":zeros,
        "empty_primitives_removed":len(dropped_primitive),
        "empty_primitive_details":dropped_primitive,
        "empty_meshes_removed":removed_meshes,
        "original_accessor_count":len(accessors),"new_accessor_count":len(dj["accessors"]),
        "original_mesh_count":len(m),"new_mesh_count":len(dj["meshes"]),
        "all_nonempty_primitives_preserved":True,
        "bytes_of_original_geometry_and_animations_unmodified":True,
        "material_definitions_untouched":dj.get("materials")==original.get("materials"),
        "glb_zero_count_accessors_remaining":sum(x.get("count",0)==0 for x in dj["accessors"]),
        "compatibility_not_yet_proven_in_Godot":True,
        "model_artistic_change":False,
        "original_sha_unchanged_after":hashlib.sha256(src.read_bytes()).hexdigest(),
        "not_an_approval":True}
    Path(report_path).parent.mkdir(parents=True,exist_ok=True)
    Path(report_path).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("empty_primitive_details","zero_count_accessor_ids")},ensure_ascii=False))
    return result


if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Uso: gltf_sanitize.py ORIGEN.glb COPIA_SANEADA.glb REPORTE.json")
    safe_prepare(sys.argv[1],sys.argv[2],sys.argv[3])
