"""COPOX G2-B: extender una superficie existente SIN solapar su borde.

El borde pertenece a una sola malla indexada; los nuevos triángulos utilizan
los índices ORIGINALES de ese borde. Se puede cerrar inferiormente la nueva
superficie, pero **no** equivale a soldarla a una segunda primitiva (rostro).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import boundary_loops,GeometryError


@dataclass(frozen=True)
class LoftResult:
    positions:np.ndarray
    faces:np.ndarray
    correspondence:np.ndarray
    rings:int
    old_vertex_count:int
    added_triangles:int
    cap_closed:bool
    boundary_loops_after:int
    degenerate_faces:int


def extend_boundary_skin(positions,faces,*, center_xz=(0.,0.),
                         front_end_y=.605,side_end_y=.615,rear_end_y=.594,
                         front_end_radius=.90,side_end_radius=.86,
                         rear_end_radius=.90,rings=12,close_bottom=True):
    """Conectar un rim íntegro al nuevo volumen craneofacial.

    Direcciones: +Z frente, Y-up, metros (valores **aportados por cassette**).
    El algoritmo no elige dimensiones ni identidad a partir de fotografías.
    No modifica el input; retorna correspondencia por índice para copiar skin.
    """
    v=np.asarray(positions,dtype=np.float64);f=np.asarray(faces,dtype=np.int64)
    cx,cz=np.asarray(center_xz,dtype=float)
    values=[front_end_y,side_end_y,rear_end_y,front_end_radius,side_end_radius,rear_end_radius,cx,cz]
    if not all(np.isfinite(values)) or not all(x>0 for x in values[3:6]):
        raise GeometryError("Valores geométricos inválidos")
    if rings<2 or type(rings)!=int:
        raise GeometryError("rings >= 2")
    if v.ndim!=2 or v.shape[1]!=3 or not np.isfinite(v).all():
        raise GeometryError("Posiciones inválidas")
    loops=boundary_loops(f)
    if len(loops)!=1:
        raise GeometryError("Se requiere un único borde simple de la superficie")
    loop=np.asarray(loops[0],dtype=int)
    original=v[loop];n=len(loop)
    theta=np.arctan2(original[:,2]-cz,original[:,0]-cx)
    sin=np.sin(theta)
    front=np.maximum(sin,0)**2
    rear=np.maximum(-sin,0)**2
    side=np.maximum(0,1-front-rear)
    bottom_y=front_end_y*front+rear_end_y*rear+side_end_y*side
    radius_factor=front*front_end_radius+rear*rear_end_radius+side*side_end_radius
    if np.any(bottom_y>original[:,1]-.012):
        raise GeometryError("La base debe quedar al menos 12mm por debajo de TODO el rim")
    radius=np.hypot(original[:,0]-cx,original[:,2]-cz)
    if np.min(radius)<.01 or np.ptp(theta)<5:
        raise GeometryError("Borde no rodea la cabeza")
    # u=0 corresponde al borde ORIGINAL. Nuevos anillos a u=1/rings .. 1.
    new=[];corr=[]
    for k in range(1,rings+1):
        t=k/rings
        s=t*t*(3-2*t)
        yy=(1-s)*original[:,1]+s*bottom_y
        rr=radius*(1+s*(radius_factor-1))
        xyz=np.column_stack([cx+rr*np.cos(theta),yy,cz+rr*np.sin(theta)])
        new.append(xyz)
        corr.extend(loop.tolist())
    new=np.concatenate(new,axis=0)
    outpos=np.vstack([v,new])
    outfaces=f.tolist()
    last=loop
    oldcount=len(v)
    for k in range(rings):
        nxt=np.arange(oldcount+k*n,oldcount+(k+1)*n,dtype=int)
        for i in range(n):
            j=(i+1)%n
            # La arista del rim original es (last[i],last[j]).
            # La extensión debe consumirla en dirección contraria.
            outfaces.extend([[int(last[j]),int(last[i]),int(nxt[i])],
                             [int(last[j]),int(nxt[i]),int(nxt[j])]])
        last=nxt
    if close_bottom:
        # Centro inferior plano dentro del volumen (cierre analítico opcional).
        closure=np.array([[cx,float(np.min(bottom_y)-.012),cz]],dtype=float)
        outpos=np.vstack([outpos,closure])
        corr.append(int(loop[0]))
        ci=len(outpos)-1
        for i in range(n):
            j=(i+1)%n
            outfaces.append([int(last[j]),int(last[i]),ci])
    ff=np.asarray(outfaces,dtype=np.int64)
    if np.any((ff[:,0]==ff[:,1])|(ff[:,1]==ff[:,2])|(ff[:,0]==ff[:,2])):
        raise GeometryError("Índices degenerados en loft")
    tri=outpos[ff]
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5
    deg=int(np.count_nonzero(area<1e-11))
    if deg:raise GeometryError(f"Triángulos degenerados: {deg}")
    after=boundary_loops(ff)
    if close_bottom and after:raise GeometryError("El cierre no logró topología cerrada")
    if not close_bottom and (len(after)!=1 or len(after[0])!=n):
        raise GeometryError("El loft abierto debería tener 1 borde de la misma cardinalidad")
    return LoftResult(outpos,ff,np.asarray(corr,dtype=int),
        rings,len(v),len(ff)-len(f),bool(close_bottom),len(after),deg)


def vertex_normals(vertices,faces):
    p=np.asarray(vertices,float);f=np.asarray(faces,int)
    tri=p[f]
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    out=np.zeros_like(p)
    for k in range(3):np.add.at(out,f[:,k],normals)
    magnitudes=np.linalg.norm(out,axis=1)
    if np.any(magnitudes<1e-12):raise GeometryError("Vértices sin normales válidas")
    return out/magnitudes[:,None]
