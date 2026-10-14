"""Mediciones geométricas reproducibles para Visual Critic.

Esto no decide si una forma es bonita: mide distancia a una superficie objetivo
registrada, conectividad y fronteras topológicas en una ROI real.
"""
from __future__ import annotations
import hashlib
import numpy as np
from copox.geometry.kernel import GeometryError


def analyze_plane_region(vertices, faces, selected_vertices, direction, plane_offset):
    p=np.asarray(vertices,dtype=np.float64)
    f=np.asarray(faces,dtype=np.int64)
    selected=np.asarray(selected_vertices)
    normal=np.array(direction,dtype=np.float64,copy=True)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all() or len(p)<3:
        raise GeometryError("Vértices no válidos")
    if f.ndim!=2 or f.shape[1]!=3 or not len(f) or f.min()<0 or f.max()>=len(p):
        raise GeometryError("Caras inválidas")
    if selected.shape!=(len(p),) or selected.dtype!=bool or not selected.any():
        raise GeometryError("ROI sin máscara booleana completa")
    if normal.shape!=(3,) or not np.isfinite(normal).all() or np.linalg.norm(normal)<1e-12:
        raise GeometryError("Dirección inválida")
    if not np.isfinite(plane_offset):
        raise GeometryError("Plano no finito")
    normal/=np.linalg.norm(normal)
    mask_faces=np.all(selected[f],axis=1)
    region_faces=f[mask_faces]
    if not len(region_faces):
        raise GeometryError("ROI sin triángulos completos")
    # conectividad por aristas de malla (no agrupar vértices que coincidan en XYZ)
    adj={int(v):set() for v in np.flatnonzero(selected)}
    counts={}
    for a,b,c in region_faces:
        for i,j in ((int(a),int(b)),(int(b),int(c)),(int(c),int(a))):
            adj[i].add(j);adj[j].add(i)
            edge=(min(i,j),max(i,j))
            counts[edge]=counts.get(edge,0)+1
    used={i for i,n in adj.items() if n}
    components=0
    seen=set()
    for start in sorted(used):
        if start in seen:continue
        components+=1
        stack=[start];seen.add(start)
        while stack:
            for v in adj[stack.pop()]:
                if v not in seen:seen.add(v);stack.append(v)
    if any(v>2 for v in counts.values()):
        raise GeometryError("ROI tiene aristas non manifold")
    excess=np.maximum(0,p[np.asarray(sorted(used),int)]@normal-float(plane_offset))
    raw_hash=hashlib.sha256(np.ascontiguousarray(p,dtype="<f8").tobytes()+
                            np.ascontiguousarray(f,dtype="<i8").tobytes()).hexdigest()
    return {
        "signed_excess_mm":float(excess.max()*1000),
        "region_topology_continuous":components==1,
        "region_components":components,
        "target_boundary_edges":int(sum(v==1 for v in counts.values())),
        "selected_vertices":int(len(used)),
        "region_triangles":int(len(region_faces)),
        "measurement_provenance":{
            "source_sha256":raw_hash,
            "measurement_method":"COPOX indexed mesh ROI plane-excess v1",
            "coordinate_system":"user-declared; coordinates remain unchanged",
            "note":"plane_offset represents a user/artist-supplied target, not an inferred artistic preference"
        }
    }
