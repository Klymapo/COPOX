"""COPOX · retopología de NUCA como cassette independiente.

Extiende SOLO una secuencia contigua de aristas del borde posterior del
cráneo, con índices originales compartidos. No modifica el rostro ni intenta
"cerrar" regiones ajenas. El resto del GLB queda congelado. La unión a Cara
sigue pendiente y se informa explícitamente.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import boundary_loops, GeometryError


@dataclass(frozen=True)
class PartialPatch:
    positions: np.ndarray
    faces: np.ndarray
    ancestry: np.ndarray
    new_faces: np.ndarray
    source_edges: np.ndarray
    report: dict


def rear_nape_patch(positions, faces, *,
                    center_xz=(0.,-.010537),
                    rear_z_max=-.075,
                    lateral_x_max=.18,
                    drop_m=.045,
                    radial_scale=.96,
                    min_edges=8,
                    profile="flat"):
    """Extend a connected back arc. No cap, no weld to facial mesh.

    The original vertex prefix and all original triangles are untouched.
    Patch has open side/bottom border by design; do NOT mark as manifold.
    """
    v=np.asarray(positions,dtype=float)
    f=np.asarray(faces,dtype=np.int64)
    if v.ndim!=2 or v.shape[1]!=3 or not np.isfinite(v).all() or len(v)<6:
        raise GeometryError("Posiciones de cráneo inválidas")
    if f.ndim!=2 or f.shape[1]!=3 or not len(f) or f.min()<0 or f.max()>=len(v):
        raise GeometryError("Caras inválidas")
    if (not 0<drop_m<=.12 or not .8<=radial_scale<=1.05 or
        not np.isfinite([rear_z_max,lateral_x_max,drop_m,radial_scale,*center_xz]).all()
        or lateral_x_max<=0 or min_edges<2):
        raise GeometryError("Parámetros locales de nuca inválidos")
    if profile not in ("flat", "eased"):
        raise GeometryError("Perfil de nuca desconocido")
    rings=boundary_loops(f)
    if len(rings)!=1:
        raise GeometryError("La primitiva craneal debe tener exactamente un contorno simple")
    rim=np.asarray(rings[0],dtype=np.int64)
    cx,cz=center_xz
    q=v[rim]
    allowed=(q[:,2]<rear_z_max) & (np.abs(q[:,0]-cx)<lateral_x_max)
    edge_allowed=allowed & np.roll(allowed,-1)
    n=len(rim)
    starts=[i for i in range(n) if edge_allowed[i] and not edge_allowed[(i-1)%n]]
    if len(starts)!=1:
        raise GeometryError(f"Se requiere un único arco posterior; encontrados {len(starts)}")
    i=starts[0];arc=[int(rim[i])]
    count=0
    while edge_allowed[i] and count<n:
        arc.append(int(rim[(i+1)%n]))
        i=(i+1)%n;count+=1
    if count<min_edges or count>=n:
        raise GeometryError(f"Arco posterior insuficiente: {count} aristas")
    chosen=np.asarray(arc,dtype=np.int64)
    base=v[chosen].copy()
    radial=np.stack((base[:,0]-cx,base[:,2]-cz),axis=1)
    # Flat is the original local probe. Eased is a separate candidate,
    # extending two curved rings without moving an original vertex.
    if profile=="eased":
        u=np.linspace(0.0,1.0,len(chosen))
        envelope=.5+.5*np.sin(np.pi*u)**2
        levels=(.40,1.0)
    else:
        envelope=np.ones(len(chosen))
        levels=(1.0,)
    layers=[]
    for level in levels:
        scale=1.0+(radial_scale-1.0)*level
        target=np.stack((cx+radial[:,0]*scale,
                         base[:,1]-drop_m*envelope*level,
                         cz+radial[:,1]*scale),axis=1)
        if (np.any(target[:,2]>=rear_z_max) or
            np.any(np.abs(target[:,0]-cx)>=lateral_x_max)):
            raise GeometryError("La extensión invade una región no permitida")
        layers.append(target)
    all_positions=np.vstack([v,*layers])
    new_id_rows=[np.arange(len(v)+i*len(chosen),
                           len(v)+(i+1)*len(chosen))
                 for i in range(len(layers))]
    faces_new=[]
    for layer_idx,new_ids in enumerate(new_id_rows):
        prev=chosen if layer_idx==0 else new_id_rows[layer_idx-1]
        for j in range(count):
            a,b=int(prev[j]),int(prev[j+1])
            na,nb=int(new_ids[j]),int(new_ids[j+1])
            faces_new.extend([[b,a,na],[b,na,nb]])
    nf=np.asarray(faces_new,dtype=np.int64)
    tri=all_positions[nf]
    areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],
                                  tri[:,2]-tri[:,0]),axis=1)/2
    if np.any(areas<1e-11):
        raise GeometryError("Parche con triángulos degenerados")
    if np.any(all_positions[nf][:,:,2]>=rear_z_max+1e-8):
        raise GeometryError("Triángulo cruza zona protegida")
    output_faces=np.vstack([f,nf])
    # Verify the new patch consumed precisely the source arc; other edges
    # of the rim are STILL open. Do not fake watertight topology.
    old_e=np.sort(np.c_[chosen[:-1],chosen[1:]],axis=1)
    original_edge=np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]),axis=0),axis=1)
    unique,cnt=np.unique(original_edge,axis=0,return_counts=True)
    boundary={tuple(edge) for edge in unique[cnt==1]}
    if any(tuple(e) not in boundary for e in old_e):
        raise GeometryError("Arco no coincide con borde abierto dirigido")
    final_edge=np.sort(np.concatenate((output_faces[:,[0,1]],
                                       output_faces[:,[1,2]],
                                       output_faces[:,[2,0]]),axis=0),axis=1)
    _,final_cnt=np.unique(final_edge,axis=0,return_counts=True)
    if np.any(final_cnt>2):
        raise GeometryError("Introducción de non-manifold")
    # Partial patch must not be represented as an approved whole model.
    report={"scope":"nuca","target_primitive":"Craneo",
            "old_vertices":int(len(v)),
            "new_vertices":int(len(all_positions)),
            "original_triangles":int(len(f)),
            "added_triangles":int(len(nf)),
            "source_arc_edges":int(count),
            "remaining_open_edges":int(np.sum(final_cnt==1)),
            "all_old_vertices_identical":True,
            "all_old_faces_identical":True,
            "new_geometry_entirely_rear":True,
            "max_drop_m":float(drop_m),
            "radial_scale":float(radial_scale),
            "profile":profile,
            "patch_rows":len(layers),
            "edge_taper_min":float(envelope.min()),
            "measured_max_vertical_drop_m":float((base[:,1]-layers[-1][:,1]).max()),
            "global_watertight":False,
            "face_primitive_changed":False,
            "original_rig_changed":False,
            "artistic_nape_improvement_proven":False,
            "join_to_face_complete":False,
            "status":"LOCAL_TECHNICAL_CANDIDATE"}
    return PartialPatch(all_positions,output_faces,np.tile(chosen,len(layers)),nf,old_e,report)
