"""COPOX · parche regional de NUCA, sin forzar aprobación facial.

Triangula SOLAMENTE aristas contiguas del borde POSTERIOR de una primitiva
existente, compartiendo índices originales. El borde frontal, rostro, ojos,
orejas y resto del GLB permanecen intactos. No certifica cierre facial.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import GeometryError,boundary_loops


@dataclass(frozen=True)
class NapePatch:
    positions: np.ndarray
    faces: np.ndarray
    parents: np.ndarray
    selected_boundary_edges: int
    added_triangles: int
    added_vertices: int
    max_displacement_m: float
    selected_old_vertex_ids: tuple
    status: str


def patch_nape_arc(
    positions, faces, *, rear_z_max=-.048,
    drop_m=.030, depth_m=.006, rings=3,
    max_displacement_m=.065
) -> NapePatch:
    p=np.asarray(positions,dtype=np.float64)
    f=np.asarray(faces,dtype=np.int64)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():
        raise GeometryError("Vértices originales inválidos")
    if f.ndim!=2 or f.shape[1]!=3 or not len(f) or f.min()<0 or f.max()>=len(p):
        raise GeometryError("Caras originales inválidas")
    if (not all(np.isfinite([rear_z_max,drop_m,depth_m,max_displacement_m]))
        or drop_m<=0 or depth_m<0 or rings not in (2,3,4,5)
        or max_displacement_m<=0):
        raise GeometryError("Parámetros de nuca inválidos")
    loops=boundary_loops(f)
    if len(loops)!=1:
        raise GeometryError("Sólo se admite cascarón con UN borde real simple")
    loop=np.asarray(loops[0],dtype=np.int64)
    nxt=np.roll(loop,-1)
    middle=(p[loop]+p[nxt])*.5
    selected=middle[:,2]<rear_z_max
    if np.count_nonzero(selected)<5:
        raise GeometryError("Arco posterior insuficiente")
    # Must be exactly one uninterrupted arc. If there are multiple
    # disconnected rear fragments, don't bridge the wrong sectors.
    starts=np.flatnonzero(selected & ~np.roll(selected,1))
    ends=np.flatnonzero(selected & ~np.roll(selected,-1))
    if len(starts)!=1 or len(ends)!=1:
        raise GeometryError("Arco posterior no contiguo; revisar contorno")
    start=int(starts[0])
    k=int(np.count_nonzero(selected))
    old_ids=[int(loop[(start+t)%len(loop)]) for t in range(k+1)]
    if len(set(old_ids))!=len(old_ids):
        raise GeometryError("Arco de nuca cerrado ambiguo")
    old=np.asarray(old_ids,dtype=np.int64)
    # taper but never collapse an entire triangle at an endpoint:
    # avoid degenerate "zero-distance" new vertices.
    ramp=np.sin(np.linspace(0,np.pi,len(old)))**.65
    ramp=np.maximum(ramp,.14)
    frames=[];parent_ids=[]
    for layer in range(1,rings+1):
        t=layer/rings
        s=t*t*(3-2*t)
        displacement=np.column_stack([
            np.zeros(len(old)),
            -drop_m*s*ramp,
            -depth_m*s*ramp
        ])
        frames.append(p[old]+displacement)
        parent_ids.extend(old.tolist())
    add=np.vstack(frames)
    displacement=np.linalg.norm(add-np.tile(p[old],(rings,1)),axis=1)
    if np.max(displacement)>max_displacement_m:
        raise GeometryError("Fuera de presupuesto de deformación de nuca")
    if np.any(add[:,2]>rear_z_max+.025):
        raise GeometryError("La extensión podría invadir la parte frontal")
    pos=np.vstack((p,add))
    ff=f.tolist()
    former=np.asarray(old,dtype=np.int64)
    base=len(p)
    for layer in range(rings):
        current=np.arange(base+layer*len(old),base+(layer+1)*len(old))
        for i in range(len(old)-1):
            aa,bb=int(former[i]),int(former[i+1])
            cc,dd=int(current[i]),int(current[i+1])
            # Consume original boundary orientation in opposite direction.
            ff.extend(((bb,aa,cc),(bb,cc,dd)))
        former=current
    out=np.asarray(ff,dtype=np.int64)
    tri=pos[out[len(f):]]
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5
    if np.any(area<1e-12):
        raise GeometryError("Triángulos degenerados; no exportar")
    # The patch is intentionally OPEN at its lower and side edges.
    # Never assert the whole head is watertight.
    return NapePatch(
        positions=pos,faces=out,parents=np.asarray(parent_ids,dtype=int),
        selected_boundary_edges=k,added_triangles=2*k*rings,
        added_vertices=len(add),
        max_displacement_m=float(np.max(displacement)),
        selected_old_vertex_ids=tuple(old_ids),
        status="LOCAL_NAPE_ONLY_UNAPPROVED",
    )
