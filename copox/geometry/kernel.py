"""COPOX · Núcleo geométrico matemático, sin motor generativo.

Operaciones puras sobre arrays NumPy; ningún I/O ni mutación de archivos.
ADVERTENCIA: Un puente sólo comparte topología si AMBOS contornos viven
en la misma malla indexada. Dos primitivas GLB son espacios de índices separados.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
import numpy as np


class GeometryError(ValueError):
    """No construir geometría cuando fallan las precondiciones anatómicas/topológicas."""


@dataclass(frozen=True)
class EllipsoidFit:
    center: np.ndarray
    radii: np.ndarray
    rms_residual: float
    points: int


def fit_axis_ellipsoid(points: np.ndarray, *, trim_quantile: float = 0.0) -> EllipsoidFit:
    """Ajuste robusto de elipsoide axis-aligned, el mismo principio de Codex.

    Requiere puntos de una superficie con cobertura espacial suficiente; NO usar
    una nube parcial frontal sin comprobar el sesgo. No sobrescribe el original.
    SciPy es dependencia gratuita y se carga sólo aquí.
    """
    from scipy.optimize import least_squares
    p = np.asarray(points, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 16 or not np.isfinite(p).all():
        raise GeometryError("points debe contener al menos 16 XYZ finitos")
    if not (0 <= trim_quantile < .2): raise GeometryError("trim_quantile inválido")
    if trim_quantile:
        lo=np.quantile(p,trim_quantile,axis=0)
        hi=np.quantile(p,1-trim_quantile,axis=0)
        sel=np.all((p>=lo)&(p<=hi),axis=1)
        p=p[sel]
    span=np.ptp(p,axis=0)
    if len(p)<16 or np.any(span < 1e-7): raise GeometryError("Muestra degenerada")
    mid=(np.max(p,axis=0)+np.min(p,axis=0))*.5
    guess=np.maximum(span*.5,1e-5)
    # Residual normalizado, para tener estabilidad en m o mm
    def loss(q):
        c=q[:3];r=np.exp(q[3:])
        return np.sum(((p-c)/r)**2,axis=1)-1
    scale=max(float(np.mean(guess)),1e-8)
    ans=least_squares(loss,np.r_[mid,np.log(guess)],
        loss="soft_l1",f_scale=.08,max_nfev=500,
        bounds=(np.r_[mid-2*span,np.log(np.maximum(guess*.25,1e-8))],
                np.r_[mid+2*span,np.log(guess*4)]))
    center=ans.x[:3];radii=np.exp(ans.x[3:])
    if not ans.success or np.any(radii<=0) or not np.isfinite(radii).all():
        raise GeometryError("Ajuste no converge")
    rms=float(np.sqrt(np.mean(loss(ans.x)**2)))
    return EllipsoidFit(center=center,radii=radii,rms_residual=rms,points=len(p))


def resample_closed(points: np.ndarray, count: int) -> np.ndarray:
    """Reparametriza un contorno cerrado 3D por distancia de arco, sin crear caras."""
    p=np.asarray(points,dtype=np.float64)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<3 or count<3 or not np.isfinite(p).all():
        raise GeometryError("Contorno inválido")
    if np.linalg.norm(p[-1]-p[0])<1e-10:p=p[:-1]
    edges=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    if len(p)<3 or np.any(edges < 1e-10):raise GeometryError("Contorno con aristas repetidas")
    lengths=np.r_[0.0,np.cumsum(edges)]
    dst=np.arange(count,dtype=float)*lengths[-1]/count
    ext=np.vstack((p,p[0]))
    return np.column_stack([np.interp(dst,lengths,ext[:,a]) for a in range(3)])


def boundary_loops(faces: np.ndarray) -> list[list[int]]:
    """Extrae contornos orientados por ÍNDICES (sin soldar posiciones UV).

    Rechaza non-manifold, aristas con winding duplicado y bordes ramificados.
    El orden es determinista. No afirma que esas aristas sean agujeros visibles.
    """
    f=np.asarray(faces,dtype=np.int64)
    if f.ndim!=2 or f.shape[1]!=3 or len(f)==0 or np.any(f<0):
        raise GeometryError("Faces triangulares no válidas")
    if np.any((f[:,0]==f[:,1])|(f[:,1]==f[:,2])|(f[:,2]==f[:,0])):
        raise GeometryError("Triángulo con índices degenerados")
    directed=np.vstack((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]))
    groups=defaultdict(list)
    for a,b in directed:
        groups[(min(int(a),int(b)),max(int(a),int(b)))].append((int(a),int(b)))
    boundary=[]
    for e,directions in groups.items():
        if len(directions)>2:raise GeometryError(f"Arista non-manifold {e}")
        if len(directions)==2 and directions[0]!=directions[1][::-1]:
            raise GeometryError(f"Winding inconsistente en arista {e}")
        if len(directions)==1:boundary.append(directions[0])
    out=defaultdict(list);inc=defaultdict(list)
    for a,b in boundary:out[a].append(b);inc[b].append(a)
    verts=set(out)|set(inc)
    if any(len(out[v])!=1 or len(inc[v])!=1 for v in verts):
        raise GeometryError("Bordes abiertos ramificados; segmentar por anatomía primero")
    visited=set();loops=[]
    for start in sorted(verts):
        if start in visited:continue
        loop=[];curr=start
        while curr not in visited:
            visited.add(curr);loop.append(curr);curr=out[curr][0]
        if curr!=start or len(loop)<3:
            raise GeometryError("Contorno incompleto o demasiado corto")
        loops.append(loop)
    return loops


def bridge_equal_loops(vertices: np.ndarray, faces: np.ndarray,
                       loop_a: list[int], loop_b: list[int],
                       *, max_gap: float | None=None) -> tuple[np.ndarray, dict]:
    """Une dos bordes de IGUAL número de vértices en UNA sola malla indexada.

    Empata B invirtiendo el recorrido para conservar winding opuesto del borde.
    Usa los IDs existentes de ambos loops: los triángulos resultantes sí comparten
    vértices con ambas superficies. No remuestrea ni inventa atributos.
    Rechaza si el puente genera degenerados o bordes non-manifold. NO certifica
    ausencia de intersecciones con el resto del personaje.
    """
    v=np.asarray(vertices,dtype=np.float64)
    f=np.asarray(faces,dtype=np.int64)
    a=np.asarray(loop_a,dtype=np.int64); b=np.asarray(loop_b,dtype=np.int64)
    if v.ndim!=2 or v.shape[1]!=3 or not np.isfinite(v).all() or len(a)<3 or len(a)!=len(b):
        raise GeometryError("Loops de tamaño diferente o vértices no válidos")
    if any(len(set(q.tolist()))!=len(q) or np.min(q)<0 or np.max(q)>=len(v) for q in (a,b)):
        raise GeometryError("Loop contiene IDs repetidos o fuera de rango")
    if set(a.tolist())&set(b.tolist()):raise GeometryError("Loops superpuestos")
    known={tuple(x) for x in boundary_loops(f)}
    def cyclic_equal(loop,other):return len(loop)==len(other) and any(tuple(np.roll(loop,i))==other for i in range(len(loop)))
    if not any(cyclic_equal(a, q) for q in known) or not any(cyclic_equal(b,q) for q in known):
        raise GeometryError("IDs no son bucles de borde reales")
    br=b[::-1]
    costs=np.array([np.sum((v[a]-v[np.roll(br,shift)])**2) for shift in range(len(a))])
    br=np.roll(br,int(np.argmin(costs)))
    gaps=np.linalg.norm(v[a]-v[br],axis=1)
    if max_gap is not None and float(np.max(gaps))>max_gap:
        raise GeometryError("Contornos demasiado alejados")
    new=[]
    for i in range(len(a)):
        t=(i+1)%len(a)
        new.extend([(a[i],br[i],a[t]),(a[t],br[i],br[t])])
    new=np.asarray(new,dtype=np.int64)
    tris=v[new]
    area=np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1)*.5
    if np.any(area<1e-12):raise GeometryError("El puente genera triángulos degenerados")
    joined=np.vstack((f,new))
    boundary_loops(joined) # guardia non-manifold + winding
    return joined,{"bridge_triangles":len(new),"paired_vertices":len(a),
                   "gap_max":float(np.max(gaps)),"gap_mean":float(np.mean(gaps)),
                   "remaining_open_loops":len(boundary_loops(joined)),
                   "same_mesh_shared_indices":True,
                   "self_intersection_checked":False,
                   "rig_weights_interpolated":False}
