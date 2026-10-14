"""COPOX G2-C: advancing front para dos bucles reales de longitud desigual.

Ningún autodiagnóstico anatómico: el caller debe proporcionar los DOS loops
VERIFICADOS por conectividad y referencias artísticas. La salida es un array
topológico, NO un GLB (exportar sin conservar skin/UV/materiales sería un error).

Diferencias con el ejemplo de Gemini:
* Las aristas boundary se determinan por incidencia DE CARAS, no por longitud.
* Sólo se admiten dos loops simples genuinos, con winding coherente.
* Es una ruta codiciosa monotónica sobre el par de loops; O(n+m) propuestas,
  sin matriz N*M ni 'cierre garantizado' de una geometría problemática.
* Se evita deformar vértices originales; no se aplica Taubin.
* Topología, índice de las caras, degeneración, escalas y límites se validan.
* Ausencia de self-intersections comprobadas = no autorización de producción.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.spatial import cKDTree
from copox.geometry.kernel import GeometryError, boundary_loops


@dataclass(frozen=True)
class AdvancingStitchResult:
    positions: np.ndarray
    faces: np.ndarray
    new_faces: np.ndarray
    report: dict


def _same_cycle(candidate, canonical):
    """Identidad del ciclo bajo rotación; su reverso NO es el mismo winding."""
    x=np.asarray(candidate,dtype=np.int64)
    y=np.asarray(canonical,dtype=np.int64)
    if len(x)!=len(y) or set(x.tolist())!=set(y.tolist()):
        return False
    loc=np.flatnonzero(y==x[0])
    return bool(len(loc)==1 and np.array_equal(x,np.roll(y,-int(loc[0]))))


def _check_mesh(vertices, faces):
    p=np.asarray(vertices,dtype=np.float64)
    f=np.asarray(faces,dtype=np.int64)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<6 or not np.isfinite(p).all():
        raise GeometryError("Vértices XYZ finitos insuficientes")
    if f.ndim!=2 or f.shape[1]!=3 or len(f)<2 or f.min()<0 or f.max()>=len(p):
        raise GeometryError("Triángulos inválidos o fuera de rango")
    loops=boundary_loops(f)  # Verifica winding + ramificaciones por ID
    return p,f,loops


def _oriented_triangles(v, a, b, *, max_gap, max_aspect_ratio):
    # Both 'a' and 'b' refer to true directed boundaries; b is reversed
    # so that the new strip consumes it in the opposite direction.
    na,nb=len(a),len(b)
    if na<3 or nb<3:
        raise GeometryError("Se necesitan al menos 3 vértices por anillo")
    # Nearest pair by KDTree: avoiding an N*M distance matrix. Sorted A and
    # deterministic KDTree tie ordering produce stable start indices.
    kd=cKDTree(v[b])
    dist,neighbor=kd.query(v[a],k=1,workers=1)
    ia=int(np.argmin(dist))
    ib=int(neighbor[ia])
    a=np.roll(a,-ia)
    b=np.roll(b,-ib)
    i=j=0
    tris=np.empty((na+nb,3),dtype=np.int64)
    diagonal_lengths=np.empty(na+nb,dtype=float)
    # Each step consumes exactly one boundary edge, including at wrap-around.
    for step in range(na+nb):
        ai=int(a[i%na]);bj=int(b[j%nb])
        if i>=na:
            side="b"
        elif j>=nb:
            side="a"
        else:
            nxt_a=int(a[(i+1)%na])
            nxt_b=int(b[(j+1)%nb])
            ca=np.linalg.norm(v[nxt_a]-v[bj])
            cb=np.linalg.norm(v[ai]-v[nxt_b])
            side="a" if ca<=cb else "b"
        if side=="a":
            nxt_a=int(a[(i+1)%na])
            tri=(ai,bj,nxt_a)
            i+=1
            length=np.linalg.norm(v[nxt_a]-v[bj])
        else:
            nxt_b=int(b[(j+1)%nb])
            tri=(ai,bj,nxt_b)
            j+=1
            length=np.linalg.norm(v[ai]-v[nxt_b])
        tris[step]=tri
        diagonal_lengths[step]=length
    if i!=na or j!=nb:
        raise GeometryError("Frente de avance incompleto")
    coords=v[tris]
    edges=np.stack((np.linalg.norm(coords[:,1]-coords[:,0],axis=1),
                    np.linalg.norm(coords[:,2]-coords[:,1],axis=1),
                    np.linalg.norm(coords[:,0]-coords[:,2],axis=1)),axis=1)
    area=np.linalg.norm(np.cross(coords[:,1]-coords[:,0],
                                 coords[:,2]-coords[:,0]),axis=1)*.5
    if np.any(area<=1e-12) or np.any(np.min(edges,axis=1)<1e-9):
        raise GeometryError("Costura degenerada o vértices coincidentes")
    ratio=np.max(edges,axis=1)/np.min(edges,axis=1)
    if np.max(ratio)>max_aspect_ratio:
        raise GeometryError(f"Triángulos muy alargados: ratio={np.max(ratio):.3f}")
    # Test EVERY cross-bridge triangle against user-defined distance, not
    # only the first nearest pair. The bridge edge is always the pair a-b.
    aa=np.isin(tris,a)
    bb=np.isin(tris,b)
    if not np.all(aa.sum(axis=1)+bb.sum(axis=1)==3):
        raise GeometryError("Triángulo incluye vértices externos al contorno")
    bridge_edges=[]
    for tri in tris:
        # exactly one or two vertices from A; compare all cross-edges
        av=tri[np.isin(tri,a)];bv=tri[np.isin(tri,b)]
        for x in av:
            for y in bv:
                bridge_edges.append(np.linalg.norm(v[x]-v[y]))
    gap_max=float(np.max(bridge_edges))
    if gap_max>max_gap:
        raise GeometryError(f"Separación {gap_max:.6f} m excede {max_gap:.6f} m")
    return tris,{"triangles":int(len(tris)),
                 "steps_a":int(i),"steps_b":int(j),
                 "max_cross_gap_m":gap_max,
                 "max_triangle_aspect_ratio":float(np.max(ratio)),
                 "min_triangle_area_m2":float(np.min(area)),
                 "max_diagonal_m":float(np.max(diagonal_lengths)),
                 "starting_pair_distance_m":float(dist[ia]),
                 "alignment":"KDTree nearest pair; B reversed; deterministic tie A first"}


def stitch_unequal_loops(vertices, faces, loop_a, loop_b, *,
                        max_gap:float, max_aspect_ratio:float=50.,
                        require_exactly_two_loops:bool=True) -> AdvancingStitchResult:
    """Return new index-connected mesh; NEVER exports/smooths original vertices.

    Selected loops must be true oriented boundaries of the SAME indexed mesh.
    A GLB with separate scene primitives must be merged into a canonical
    index space with skin/UV/material attributes handled outside this kernel.
    """
    p,f,loops=_check_mesh(vertices,faces)
    if require_exactly_two_loops and len(loops)!=2:
        raise GeometryError(f"Expected exactly 2 proven true loops, found {len(loops)}")
    if not np.isfinite(max_gap) or max_gap<=0 or not np.isfinite(max_aspect_ratio) or max_aspect_ratio<1:
        raise GeometryError("max_gap / max_aspect_ratio inválidos")
    la=np.asarray(loop_a,dtype=np.int64);lb=np.asarray(loop_b,dtype=np.int64)
    if not any(_same_cycle(la,x) for x in loops) or not any(_same_cycle(lb,x) for x in loops):
        raise GeometryError("El anillo no corresponde a un borde dirigido REAL de la malla")
    if set(la.tolist())&set(lb.tolist()):
        raise GeometryError("Loops comparten vértices; topología ambigua")
    # The winding of B is *opposed* when woven into a strip.
    tris,stats=_oriented_triangles(p,la,lb[::-1],max_gap=max_gap,
                                    max_aspect_ratio=max_aspect_ratio)
    out=np.vstack((f,tris))
    remaining=boundary_loops(out)
    if require_exactly_two_loops and remaining:
        raise GeometryError("La costura NO eliminó los bucles anteriores")
    report={**stats,"loops_before":len(loops),
            "loops_after":len(remaining),
            "input_vertices_unchanged":True,
            "same_index_space":True,
            "output_winding_checked":True,
            "output_nonmanifold_edges_checked":True,
            "self_intersections_checked":False,
            "skin_uv_material_export_checked":False,
            "artistic_references_approved":False,
            "godot_import_checked":False,
            "production_ready":False,
            "warnings":["Un manifold indexado aún puede autointersectarse",
                        "No equivale a semejanza artística",
                        "No exportar GLB sin serializador que preserve UV, skin y material por cara"]}
    return AdvancingStitchResult(p.copy(),out,tris,report)
