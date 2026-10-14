"""COPOX G2 · Análisis de contornos de frontera, NO soldadura.
Opera en índices originales o copia espacial cuantizada sólo analítica.
Un loop topológico cerrado no implica que sea la unión anatómica correcta.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
from copox.geometry.kernel import GeometryError


def inspect_contour_graph(vertices: np.ndarray,faces: np.ndarray,
                          target_rim: np.ndarray, *,
                          weld_decimals: int = 6,
                          correspondence_distance: float = .020) -> dict:
    v=np.asarray(vertices,dtype=float); f=np.asarray(faces,dtype=np.int64)
    r=np.asarray(target_rim,dtype=float)
    if v.ndim!=2 or v.shape[1]!=3 or not len(v) or not np.isfinite(v).all():
        raise GeometryError("positions inválidas")
    if f.ndim!=2 or f.shape[1]!=3 or not len(f) or f.min()<0 or f.max()>=len(v):
        raise GeometryError("triángulos inválidos")
    if r.ndim!=2 or r.shape[1]!=3 or len(r)<3 or not np.isfinite(r).all():
        raise GeometryError("rim inválido")
    if not 0<=weld_decimals<=12 or correspondence_distance<=0:
        raise GeometryError("parametrización inválida")
    points,inv=np.unique(np.round(v,weld_decimals),axis=0,return_inverse=True)
    ff=inv[f]
    if np.any((ff[:,0]==ff[:,1])|(ff[:,1]==ff[:,2])|(ff[:,0]==ff[:,2])):
        return {"state":"BLOCKED_DEGENERATE_WELD","closed_components":[],"stitch_ready":False}
    e=np.sort(np.concatenate((ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]])),axis=0),axis=1)
    edges,counts=np.unique(e,axis=0,return_counts=True)
    boundary=edges[counts==1]
    nm=int(np.sum(counts>2))
    graph=defaultdict(set)
    for a,b in boundary:
        a=int(a);b=int(b)
        graph[a].add(b);graph[b].add(a)
    seen=set();items=[]
    for start in sorted(graph):
        if start in seen:continue
        stack=[start];seen.add(start);part=[]
        while stack:
            x=stack.pop();part.append(x)
            for n in sorted(graph[x]):
                if n not in seen:seen.add(n);stack.append(n)
        degrees=[len(graph[v]) for v in part]
        nodes=np.asarray(sorted(part),dtype=int)
        xyz=points[nodes]
        # coverage tells if rim points have geometrically near representatives,
        # NOT that they connect in proper order.
        d,_=cKDTree(xyz).query(r,k=1)
        items.append({
            "vertices":int(len(nodes)),
            "edges":int(sum(degrees)//2),
            "closed_simple_cycle":bool(len(nodes)>=3 and all(x==2 for x in degrees)),
            "branch_vertices":int(sum(x>2 for x in degrees)),
            "endpoint_vertices":int(sum(x==1 for x in degrees)),
            "rim_nearby_fraction":round(float(np.mean(d<=correspondence_distance)),5),
            "rim_nearby_count":int(np.count_nonzero(d<=correspondence_distance)),
            "distance_to_rim_p95_mm":round(float(np.percentile(d,95)*1000),3),
            "distance_to_rim_median_mm":round(float(np.median(d)*1000),3),
            "bounds_min":xyz.min(axis=0).round(6).tolist(),
            "bounds_max":xyz.max(axis=0).round(6).tolist(),
        })
    items.sort(key=lambda z:(-z["rim_nearby_count"],-z["vertices"]))
    closed=[x for x in items if x["closed_simple_cycle"]]
    viable=[x for x in closed if x["rim_nearby_fraction"]>=.95]
    return {"state":"INSPECTED_NOT_WELDED",
        "quantized_positions":len(points),
        "boundary_edges":int(len(boundary)),
        "nonmanifold_edges":nm,
        "boundary_components":len(items),
        "closed_simple_cycles":len(closed),
        "potential_full_ring_cycles":len(viable),
        "target_rim_vertices":int(len(r)),
        "distance_limit_m":float(correspondence_distance),
        "highest_rim_coverage":max((z["rim_nearby_fraction"] for z in items),default=0),
        "components":items[:24],
        "stitch_ready":False,
        "why_not_ready":"El análisis de ciclos no verifica winding, anatomía, UV/skin ni ausencia de autointersecciones; requiere segmentación/protecciones confirmadas y homologación real.",
        "semantic_guard":"No convertir automáticamente un ciclo pequeño de ojo/oreja en contorno facial.",
    }
