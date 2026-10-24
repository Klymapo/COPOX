"""COPOX · Surface Stitch: ensamblar DOS superficies en UNA topología indexada.

No es todavía un exportador glTF: los materiales se conservan como IDs POR CARA.
Para convertir a GLB sin perder topología/UV/rig hará falta un serializador
validado que no vuelva a separar los índices entre primitivas.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from copox.geometry.kernel import GeometryError, bridge_equal_loops


@dataclass(frozen=True)
class MeshPart:
    positions: np.ndarray
    faces: np.ndarray
    attributes: dict[str,np.ndarray]
    material_id: int = 0


@dataclass(frozen=True)
class StitchResult:
    positions: np.ndarray
    faces: np.ndarray
    attributes: dict[str,np.ndarray]
    face_materials: np.ndarray
    report: dict


_ALLOWED={"NORMAL","TEXCOORD_0","TEXCOORD_1","COLOR_0","JOINTS_0","WEIGHTS_0"}


def stitch_parts(a: MeshPart,b: MeshPart,
                 loop_a: list[int],loop_b: list[int],
                 *, max_gap: float,bridge_material: int=0,
                 morph_targets_present: bool=False) -> StitchResult:
    """Conecta bordes verdaderos entre partes en una MALLA indexada compartida.

    Requiere loops del mismo tamaño. Copia atributos originales sin modificar
    y no añade vértices, por lo que pesos/UV quedan definidos. Rechaza atributos
    faltantes/incompatibles. Verificación de auto-intersecciones queda pendiente.
    """
    if morph_targets_present:
        raise GeometryError("Morph targets sin transferencia certificada")
    def verify(part):
        p=np.asarray(part.positions,dtype=float)
        f=np.asarray(part.faces,dtype=np.int64)
        if p.ndim!=2 or p.shape[1]!=3 or len(p)<3 or not np.isfinite(p).all():
            raise GeometryError("Positions inválidos")
        if f.ndim!=2 or f.shape[1]!=3 or len(f)==0 or f.min()<0 or f.max()>=len(p):
            raise GeometryError("Triángulos inválidos")
        if set(part.attributes)-_ALLOWED:
            raise GeometryError("Atributo no soportado, no descartar silenciosamente")
        if ("JOINTS_0" in part.attributes)!=("WEIGHTS_0" in part.attributes):
            raise GeometryError("JOINTS_0 y WEIGHTS_0 son inseparables")
        for key,value in part.attributes.items():
            v=np.asarray(value)
            if len(v)!=len(p) or not np.isfinite(v).all():
                raise GeometryError("Atributos fuera de rango")
            if key in ("JOINTS_0","WEIGHTS_0") and v.shape[1:]!=(4,):
                raise GeometryError("Pesos/joints requieren cuatro componentes")
        if "WEIGHTS_0" in part.attributes:
            w=np.asarray(part.attributes["WEIGHTS_0"],dtype=float)
            if np.any(w<0) or np.any(abs(w.sum(axis=1)-1)>1e-3):
                raise GeometryError("Suma de pesos inválida")
        if type(part.material_id)!=int or part.material_id<0:
            raise GeometryError("Material debe ser entero no negativo")
        return p,f
    va,fa=verify(a);vb,fb=verify(b)
    if set(a.attributes)!=set(b.attributes):
        raise GeometryError("Materiales/UV/skin de las piezas incompatibles")
    if max_gap <= 0 or not np.isfinite(max_gap):
        raise GeometryError("max_gap debe ser positivo")
    for name in a.attributes:
        if a.attributes[name].shape[1:]!=b.attributes[name].shape[1:]:
            raise GeometryError("Dimensiones de atributo incompatibles: "+name)
    vertices=np.vstack((va,vb))
    faces=np.vstack((fa,fb+len(va)))
    cb=[int(i)+len(va) for i in loop_b]
    joined,stats=bridge_equal_loops(vertices,faces,loop_a,cb,max_gap=max_gap)
    attrs={k:np.concatenate((np.asarray(a.attributes[k]),np.asarray(b.attributes[k])),axis=0)
           for k in a.attributes}
    labels=np.r_[np.full(len(fa),a.material_id,dtype=np.int32),
                 np.full(len(fb),b.material_id,dtype=np.int32),
                 np.full(stats["bridge_triangles"],bridge_material,dtype=np.int32)]
    stats.update({"original_vertices_retained":True,
                  "material_ids_preserved_per_face":True,
                  "exported_glb_verified":False,
                  "glb_export_warning":"Un export por primitivas puede volver a partir la topología",
                  "self_intersection_checked":False})
    return StitchResult(vertices,joined,attrs,labels,stats)
