"""COPOX: extensión PARCIAL del borde de nuca sin cambiar frente/cara.

Genera sólo triángulos traseros sobre el borde real del cráneo.
Quedan abiertos los extremos de la banda: NO es cabeza sellada.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import boundary_loops,GeometryError


@dataclass(frozen=True)
class PartialLoft:
    positions:np.ndarray
    faces:np.ndarray
    source_vertex_ids:np.ndarray
    created_triangles:int
    selected_boundary_edges:int
    unchanged_positions:int
    report:dict


def extend_rear_arc(positions, faces, *, rear_direction=(0.,-1.),
                    sector_threshold=.30, drop_m=.026,
                    radius_factor=.975, center_xz=(0.,0.)):
    """Extend a connected rear arc. +Z face; -Z nape.
    The input arrays remain unchanged.
    """
    v=np.asarray(positions,dtype=float)
    f=np.asarray(faces,dtype=np.int64)
    if v.ndim!=2 or v.shape[1]!=3 or not np.isfinite(v).all() or f.ndim!=2 or f.shape[1]!=3:
        raise GeometryError("Invalid vertex/face array")
    if not (0<sector_threshold<1 and .002<=drop_m<=.08 and .7<=radius_factor<=1.10):
        raise GeometryError("Unsafe nape parameters")
    rear=np.asarray(rear_direction,dtype=float)
    if rear.shape!=(2,) or not np.isfinite(rear).all() or np.linalg.norm(rear)==0:
        raise GeometryError("Invalid rear orientation")
    rear=rear/np.linalg.norm(rear)
    cycles=boundary_loops(f)
    if len(cycles)!=1:
        raise GeometryError("Nape extension requires one valid boundary loop")
    loop=np.asarray(cycles[0],dtype=int)
    cx,cz=center_xz
    directions=v[loop][:,[0,2]]-np.asarray([cx,cz])
    lengths=np.linalg.norm(directions,axis=1)
    if np.any(lengths<.02):
        raise GeometryError("Boundary too close to center")
    directions=directions/lengths[:,None]
    cosine=directions@rear
    approved=cosine>sector_threshold
    chosen_edges=np.flatnonzero(approved & np.roll(approved,-1))
    if len(chosen_edges)<4 or len(chosen_edges)>=len(loop)-3:
        raise GeometryError("Rear sector too small or not localized")
    unique_ids=np.unique(np.concatenate((loop[chosen_edges],
                         loop[(chosen_edges+1)%len(loop)])))
    original=v[unique_ids]
    radial=original[:,[0,2]]-np.asarray([cx,cz])
    new_positions=original.copy()
    new_positions[:,1]-=drop_m
    new_positions[:,0]=cx+radial[:,0]*radius_factor
    new_positions[:,2]=cz+radial[:,1]*radius_factor
    expanded=np.vstack((v,new_positions))
    lookup={int(old):len(v)+i for i,old in enumerate(unique_ids)}
    new_faces=[]
    for idx in chosen_edges:
        a=int(loop[idx]);b=int(loop[(idx+1)%len(loop)])
        u=lookup[a];w=lookup[b]
        new_faces.extend(((b,a,u),(b,u,w)))
    triangles=np.asarray(new_faces,dtype=np.int64)
    xyz=expanded[triangles]
    areas=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)*.5
    if np.any(areas<=1e-12):
        raise GeometryError("Degenerate triangles")
    complete=np.vstack((f,triangles))
    out_loops=boundary_loops(complete)
    if len(out_loops)!=1:
        raise GeometryError("Partial loft introduced branch or disconnected boundary")
    if not np.array_equal(expanded[:len(v)],v):
        raise GeometryError("Original vertices mutated")
    return PartialLoft(expanded,complete,unique_ids,len(new_faces),
      int(len(chosen_edges)),len(v),{
        "local_region":"nuca",
        "added_vertices":len(unique_ids),
        "added_triangles":len(new_faces),
        "boundary_edges_used":len(chosen_edges),
        "remaining_open_loops":len(out_loops),
        "original_vertex_positions_unchanged":True,
        "front_sector_selected":bool(np.any(cosine[chosen_edges]<0)),
        "facial_primitive_modified":False,
        "face_to_cap_seam_welded":False,
        "artistic_approval":False,
        "full_mesh_watertight":False,
        "no_automatic_promotion":True,
      })
