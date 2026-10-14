"""COPOX G2 · Clasificación anatómica conservadora por triángulo.

La ROI se especifica por un cassette, nunca se presupone para otro personaje.
No borra caras, no escribe GLB. Si una sola esquina está protegida,
la cara ENTERA queda congelada. Distancias en unidades del modelo.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.spatial import cKDTree
from copox.geometry.kernel import GeometryError


@dataclass(frozen=True)
class RegionBox:
    name: str
    minimum: tuple[float,float,float]
    maximum: tuple[float,float,float]


@dataclass(frozen=True)
class G2RegionMap:
    protected: np.ndarray
    review: np.ndarray
    candidate: np.ndarray
    unaffected: np.ndarray
    protection_counts: dict
    nearest_rim_distances: np.ndarray
    rim_sector_coverage: float
    candidate_sector_count: int
    rim_vertices: int
    report: dict


def classify_anatomic_band(
    positions: np.ndarray, faces: np.ndarray,
    cap_boundary_positions: np.ndarray, boxes: list[RegionBox],
    *, seam_distance: float, clearance: float,
    angle_center_xz: tuple[float,float]=(0.,0.),
    near_seam_factor: float = 2.0,
) -> G2RegionMap:
    p=np.asarray(positions,dtype=np.float64)
    f=np.asarray(faces,dtype=np.int64)
    r=np.asarray(cap_boundary_positions,dtype=np.float64)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all() or len(p)<3:
        raise GeometryError("Posiciones no válidas")
    if f.ndim!=2 or f.shape[1]!=3 or not len(f) or f.min()<0 or f.max()>=len(p):
        raise GeometryError("Triángulos no válidos")
    if r.ndim!=2 or r.shape[1]!=3 or len(r)<8 or not np.isfinite(r).all():
        raise GeometryError("Rim incompleto")
    if seam_distance<=0 or not np.isfinite(seam_distance) or clearance<=0 or not np.isfinite(clearance):
        raise GeometryError("Distancia de banda inválida")
    if not isinstance(boxes,list) or not boxes or len({b.name for b in boxes})!=len(boxes):
        raise GeometryError("Las cajas de protección requieren nombres únicos")
    corner=p[f]
    protected=np.zeros(len(f),dtype=bool)
    counts={}
    for box in boxes:
        lower=np.asarray(box.minimum,dtype=float);upper=np.asarray(box.maximum,dtype=float)
        if lower.shape!=(3,) or upper.shape!=(3,) or np.any(lower>=upper) or not np.isfinite(lower).all() or not np.isfinite(upper).all():
            raise GeometryError(f"Caja inválida: {box.name}")
        corner_inside=np.all((corner>=lower)&(corner<=upper),axis=2)
        mask=np.any(corner_inside,axis=1)
        counts[box.name]=int(np.count_nonzero(mask))
        protected|=mask

    centroids=corner.mean(axis=1)
    dist,nearest=cKDTree(r).query(centroids,k=1)
    # Rim height interpolated periodically by anatomical angle. Not a vertex-
    # neighbor weld or a contour by itself: it only labels a corridor.
    cx,cz=angle_center_xz
    theta=np.mod(np.arctan2(r[:,2]-cz,r[:,0]-cx),2*np.pi)
    ordered=np.argsort(theta)
    u=theta[ordered];h=r[ordered,1]
    if np.any(np.diff(u)<1e-8):
        raise GeometryError("Rim sin angularidad 1-a-1; no inferir altura")
    q=np.mod(np.arctan2(centroids[:,2]-cz,centroids[:,0]-cx),2*np.pi)
    periodic_x=np.r_[u[-1]-2*np.pi,u,u[0]+2*np.pi]
    periodic_y=np.r_[h[-1],h,h[0]]
    border_y=np.interp(q,periodic_x,periodic_y)
    signed_vertical=centroids[:,1]-border_y
    candidate=(dist<=seam_distance)&(signed_vertical>=-clearance)&~protected
    review=(dist<=seam_distance*near_seam_factor)&~candidate&~protected
    unaffected=~(candidate|review|protected)
    selected=np.unique(nearest[candidate])
    sector_coverage=float(len(selected)/len(r))
    if any(np.any(mask & candidate) for mask in [protected,review]):
        raise GeometryError("Máscaras solapadas")
    report={"faces_total":int(len(f)), "protected":int(protected.sum()),
       "review":int(review.sum()),"candidate":int(candidate.sum()),
       "unaffected":int(unaffected.sum()),
       "candidate_rim_sectors":int(len(selected)),
       "total_rim_sectors":int(len(r)),
       "rim_sector_coverage":sector_coverage,
       "band_distance_m":float(seam_distance),
       "clearance_m":float(clearance),
       "candidate_max_distance_m":float(dist[candidate].max()) if candidate.any() else None,
       "protected_preserved_by_construction":True,
       "cut_allowed":False,
       "limitations":["Angular/cKDTree selection is a corridor, not an anatomical edge loop",
                      "Semantic boxes must be artist-verified with every reference",
                      "Removing candidate faces can create new open boundaries"]}
    return G2RegionMap(protected.copy(),review.copy(),candidate.copy(),
        unaffected.copy(),counts,dist.copy(),sector_coverage,
        len(selected),len(r),report)
