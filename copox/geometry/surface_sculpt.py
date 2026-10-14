"""COPOX · Scully: edición paramétrica regional, sin tocar inputs.

Las coordenadas y dimensiones son provistas por cada cassette; ninguna
convención de ejes está incrustada. No modifica atributos GLB por sí mismo.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import GeometryError


@dataclass(frozen=True)
class SculptResult:
    positions: np.ndarray
    changed_vertices: int
    maximum_displacement: float
    displacement_rms: float


def flatten_surface(
    positions: np.ndarray,
    *,
    direction: np.ndarray,
    target_projection: float,
    region_center: np.ndarray,
    region_radii: np.ndarray,
    strength: float = 1.0,
    falloff: float = 0.25,
    protected: np.ndarray | None = None,
    max_displacement: float | None = None,
) -> SculptResult:
    """Aplana una región hacia el plano dot(p, direction)=target_projection.

    Selección radial elíptica en el plano perpendicular a direction;
    sólo desplaza puntos que sobresalen en dirección positiva.
    Mantiene sin cambios todos los vértices fuera de la ROI y protegidos.
    Este es un paso de modelado, no de retopología o auto-collision.
    """
    p = np.asarray(positions, dtype=np.float64)
    d = np.array(direction, dtype=np.float64, copy=True)
    center = np.asarray(region_center, dtype=np.float64)
    radii = np.asarray(region_radii, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) == 0 or not np.isfinite(p).all():
        raise GeometryError("Posiciones XYZ no válidas")
    if d.shape != (3,) or center.shape != (3,) or radii.shape != (3,):
        raise GeometryError("Direction, center y radii deben ser VEC3")
    if not np.isfinite(d).all() or not np.isfinite(radii).all() or np.any(radii <= 0):
        raise GeometryError("Dirección o radios no válidos")
    if not np.isfinite(center).all() or not np.isfinite(target_projection):
        raise GeometryError("Centro/plano no finitos")
    if not (0 <= strength <= 1) or not (0 < falloff <= 1):
        raise GeometryError("Strength debe estar en [0,1]; falloff en (0,1]")
    norm = float(np.linalg.norm(d))
    if norm < 1e-10:
        raise GeometryError("Dirección sin norma")
    d /= norm
    if max_displacement is not None and (not np.isfinite(max_displacement) or max_displacement <= 0):
        raise GeometryError("Límite de desplazamiento inválido")
    guard = np.zeros(len(p), dtype=bool) if protected is None else np.asarray(protected)
    if guard.shape != (len(p),) or guard.dtype != bool:
        raise GeometryError("La máscara protegida debe ser booleana por vértice")
    lateral = (p - center) - np.outer((p - center) @ d, d)
    # Eje arbitrario: región elipsoidal; radii en el espacio XYZ del cassette.
    r = np.sqrt(np.sum((lateral / radii) ** 2, axis=1))
    t = np.clip((r - (1.0 - falloff)) / falloff, 0, 1)
    smooth = 1.0 - (t * t * (3 - 2 * t))
    protrusion = np.maximum(0.0, p @ d - float(target_projection))
    step = protrusion * smooth * strength
    step[guard] = 0.0
    biggest = float(np.max(step))
    if max_displacement is not None and biggest > max_displacement + 1e-10:
        raise GeometryError("Desplazamiento excede presupuesto: no recortar silenciosamente")
    out = p - step[:, None] * d[None, :]
    return SculptResult(out, int(np.count_nonzero(step > 1e-10)),
                        biggest, float(np.sqrt(np.mean(step ** 2))))
