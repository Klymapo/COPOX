"""COPOX · Anatomic Cut: recorte de triángulos preservando atributos glTF.

El recorte es un plano en el espacio XYZ declarado; conserva el semiespacio
dot(P, normal) <= offset. Rechaza morph targets, atributos no conocidos y
cualquier problema de skinning en vez de exportar silenciosamente un GLB roto.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import GeometryError

_ALLOWED = {"POSITION", "NORMAL", "TEXCOORD_0", "TEXCOORD_1", "COLOR_0",
            "JOINTS_0", "WEIGHTS_0"}


@dataclass(frozen=True)
class CutResult:
    attributes: dict[str, np.ndarray]
    faces: np.ndarray
    source_faces: np.ndarray
    clipped_faces: int
    removed_faces: int
    added_vertices: int
    protected_faces_preserved: int


def cut_plane(attributes: dict[str, np.ndarray], faces: np.ndarray,
              normal: np.ndarray, offset: float, *,
              protected_faces: np.ndarray | None = None,
              morph_targets_present: bool = False) -> CutResult:
    """Recorta cara a cara; preserva triángulos protegidos COMPLETOS.

    Los cruces sobre la misma arista comparten un índice nuevo. UV y normales
    se interpolan; JOINTS_0/WEIGHTS_0 se combinan en hasta 4 influencias.
    La protección puede dejar polígonos fuera del plano a propósito: el método
    no afirma que la superficie final sea cerrada ni libre de intersecciones.
    """
    if morph_targets_present:
        raise GeometryError("Morph targets requieren un adaptador explícito")
    if not isinstance(attributes, dict) or "POSITION" not in attributes:
        raise GeometryError("Falta POSITION")
    if set(attributes) - _ALLOWED:
        raise GeometryError("Atributos no soportados: " + ",".join(sorted(set(attributes)-_ALLOWED)))
    if ("JOINTS_0" in attributes) != ("WEIGHTS_0" in attributes):
        raise GeometryError("JOINTS_0 y WEIGHTS_0 deben aparecer juntos")
    attrs = {k: np.asarray(v) for k, v in attributes.items()}
    pos = np.asarray(attrs["POSITION"], dtype=np.float64)
    idx = np.asarray(faces, dtype=np.int64)
    n = np.asarray(normal, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3 or len(pos) < 3 or not np.isfinite(pos).all():
        raise GeometryError("POSITION inválido")
    if idx.ndim != 2 or idx.shape[1] != 3 or (len(idx) and (idx.min() < 0 or idx.max() >= len(pos))):
        raise GeometryError("Índices de triángulos inválidos")
    if n.shape != (3,) or not np.isfinite(n).all() or np.linalg.norm(n) < 1e-10 or not np.isfinite(offset):
        raise GeometryError("Plano inválido")
    n /= np.linalg.norm(n)
    for k, val in attrs.items():
        if len(val) != len(pos) or not np.isfinite(val).all():
            raise GeometryError(f"Atributos inválidos para {k}")
        if k in ("JOINTS_0", "WEIGHTS_0") and val.shape[1:] != (4,):
            raise GeometryError("El kernel admite hasta 4 pesos y juntas por vértice")
    if "WEIGHTS_0" in attrs:
        weights=np.asarray(attrs["WEIGHTS_0"], dtype=float)
        if np.any(weights < 0) or np.any(abs(weights.sum(axis=1)-1.0)>1e-3):
            raise GeometryError("Pesos de origen inválidos")
    protected = (np.zeros(len(idx), dtype=bool) if protected_faces is None
                 else np.asarray(protected_faces))
    if protected.shape != (len(idx),) or protected.dtype != bool:
        raise GeometryError("protected_faces inválido")
    signed = pos @ n - float(offset)
    keep = signed <= 1e-10
    out = {k: list(v) for k, v in attrs.items()}
    new_faces=[];source_faces=[]; crossings={}
    clipped=0; removed=0
    def blend(a,b,t):
        values={}
        for name, old in attrs.items():
            if name.startswith("JOINTS_") or name.startswith("WEIGHTS_"):continue
            val=(1-t)*old[a].astype(float)+t*old[b].astype(float)
            if name=="NORMAL":
                magnitude=np.linalg.norm(val)
                if magnitude>1e-12:val/=magnitude
            values[name]=val
        if "JOINTS_0" in attrs:
            weights={}
            for v,factor in ((a,1-t),(b,t)):
                for bone,weight in zip(attrs["JOINTS_0"][v],attrs["WEIGHTS_0"][v]):
                    weights[int(bone)]=weights.get(int(bone),0.)+factor*float(weight)
            ranked=sorted(weights.items(),key=lambda pair:(-pair[1],pair[0]))[:4]
            s=sum(w for _,w in ranked)
            if s<=1e-12:raise GeometryError("No hay pesos válidos para nueva intersección")
            values["JOINTS_0"]=np.array([x for x,_ in ranked]+[0]*(4-len(ranked)),dtype=attrs["JOINTS_0"].dtype)
            values["WEIGHTS_0"]=np.array([w/s for _,w in ranked]+[0]*(4-len(ranked)),dtype=float)
        return values
    def crossing(a,b):
        key=(min(a,b),max(a,b))
        if key in crossings:return crossings[key]
        t=float(signed[a]/(signed[a]-signed[b]))
        if not (0<=t<=1) or not np.isfinite(t):raise GeometryError("Intersección no válida")
        new_idx=len(out["POSITION"])
        vals=blend(a,b,t)
        for key2 in out:out[key2].append(vals[key2])
        crossings[key]=new_idx
        return new_idx
    for fi,tri in enumerate(idx):
        if protected[fi]:
            new_faces.append([int(x) for x in tri]);source_faces.append(fi)
            continue
        if not np.any(keep[tri]):
            removed+=1
            continue
        if np.all(keep[tri]):
            new_faces.append([int(x) for x in tri]);source_faces.append(fi)
            continue
        clipped+=1;poly=[]
        for a,b in zip(tri,np.roll(tri,-1)):
            a=int(a);b=int(b)
            if keep[a]:poly.append(a)
            if keep[a] != keep[b]:poly.append(crossing(a,b))
        # Collinear boundary crossings can create duplicate indices.
        poly=[value for i,value in enumerate(poly) if i==0 or value!=poly[i-1]]
        if len(poly)>1 and poly[0]==poly[-1]:poly.pop()
        for k in range(1,len(poly)-1):
            nf=[poly[0],poly[k],poly[k+1]]
            if len(set(nf))<3:continue
            xyz=np.asarray([out["POSITION"][v] for v in nf],dtype=float)
            if np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))<1e-12:continue
            new_faces.append(nf);source_faces.append(fi)
    result_attrs={}
    for key, val in attrs.items():
        desired=np.float64 if key in ("POSITION","NORMAL","WEIGHTS_0") else val.dtype
        result_attrs[key]=np.asarray(out[key],dtype=desired)
    return CutResult(result_attrs,np.asarray(new_faces,dtype=np.int64).reshape((-1,3)),
                     np.asarray(source_faces,dtype=np.int64),
                     clipped,removed,len(crossings),int(protected.sum()))
