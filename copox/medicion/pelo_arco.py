"""SENKU · arco del pelo desde la hoja de referencia (Admin, 19 oct 2026: "Falta una forma de hacer el arco. Usa SENKU").

El arco (el contorno de la cabeza con pelo: cuánto sube, cuánto se abre a los lados y cómo cae atrás) se mide en la hoja
de 4 vistas (refs/personajes/joven-rubio-4-vistas.jpg) y se lleva a 3D con un CASCO VISUAL:
  1. Por vista (frente, perfil, espalda): máscara de la cabeza = pelo ∪ piel (sin ropa ni fondo), huecos rellenos.
  2. Alineación con el esqueleto del modelo (sin mirar la cabeza, para no hacer trampa): piso (suela más baja) y línea
     de hombros (los brazos en T) dan escala y altura; el centro del cuerpo da la posición horizontal. En perfil la
     escala es la de frente (misma hoja) y el centro horizontal sale del torso.
  3. Casco: desde el centro del cráneo, por cada dirección, el radio máximo cuyo punto proyecta DENTRO de la cabeza en
     todas las vistas. Con tres vistas ortogonales el corte horizontal sale rectangular: se redondea con una
     superelipse que pasa por los mismos extremos.
  4. `arco(H, ...)` devuelve el radio objetivo de la superficie exterior del pelo por dirección. La receta pone la
     base del cráneo debajo y los mechones encima siguiendo ese arco.
`comparar(...)` mide IoU de la silueta de la cabeza modelo contra la hoja por vista y por franja (arriba = pelo).
"""
from __future__ import annotations

import numpy as np
from PIL import Image

REF = "refs/personajes/joven-rubio-4-vistas.jpg"


from . import senku_ref as sr

# (la hoja, la alineación y la comparación viven ahora en senku_ref; aquí quedan nombres de compatibilidad)
_uv = sr._uv
esqueleto = sr.esqueleto
mascara_modelo = sr.mascara_modelo


def vistas_ref(ruta=REF):
    return sr.cargar_hoja(ruta)


def alinear(ref, joints, torso_z=None, consistente=True):
    return sr.alinear(ref, joints, consistente=consistente)[0]


def casco(c, D, ref, al, r0, r1, paso=0.0015, vistas=("frente", "perfil", "espalda"), n_super=3.0):
    """Radio máximo (desde c, por dirección D) que queda dentro de la cabeza en todas las vistas. Busca de r0 a r1."""
    rs = np.arange(r0, r1, paso)
    dentro = np.ones((len(D), len(rs)), bool)
    for v in vistas:
        e, u0, piso = al[v]
        m = ref[v]["cabeza"]
        for k, r in enumerate(rs):
            P = c + D * r
            u, y = _uv(P, v)
            col = np.round(u0 + u * e).astype(int); fil = np.round(piso - y * e).astype(int)
            ok = (col >= 0) & (col < m.shape[1]) & (fil >= 0) & (fil < m.shape[0])
            ins = np.zeros(len(D), bool)
            ins[ok] = m[fil[ok], col[ok]]
            dentro[:, k] &= ins
    # radio = último r dentro, contando desde adentro sin huecos
    fuera = ~dentro
    primero_fuera = np.where(fuera.any(1), fuera.argmax(1), len(rs))
    R = r0 + paso * np.maximum(primero_fuera - 1, 0)
    # redondear el corte horizontal (tres vistas ortogonales dejan esquinas de caja): superelipse por los extremos
    dx, dz = D[:, 0], D[:, 2]
    hor = np.sqrt(dx * dx + dz * dz) + 1e-9
    # extremos por elevación (franjas de 5°)
    el = np.degrees(np.arcsin(np.clip(D[:, 1], -1, 1)))
    Rr = R.copy()
    for e0 in range(-90, 90, 5):
        s = (el >= e0) & (el < e0 + 5)
        if s.sum() < 8:
            continue
        X = (R[s] * dx[s]); Z = (R[s] * dz[s])
        ax, bz = np.abs(X).max(), np.abs(Z).max()
        # radio de la superelipse en la dirección horizontal de cada punto (en el plano de la franja)
        cx, cz = np.abs(dx[s] / hor[s]), np.abs(dz[s] / hor[s])
        rh = 1.0 / ((cx / max(ax, 1e-6)) ** n_super + (cz / max(bz, 1e-6)) ** n_super) ** (1 / n_super)
        Rr[s] = np.minimum(R[s], rh / np.maximum(hor[s], 1e-3))   # a radio r la extensión horizontal es r·hor
    return Rr, R


def comparar(V, T, ref, al, y_corte_px=None, salida=None):
    """Compatibilidad: IoU de la cabeza contra la hoja (usa senku_ref.comparar)."""
    return sr.comparar(V, T, ref, al, "cabeza", salida=salida)


def arco(H, c, ref, al, espesor, r1=0.40, minimo=0.0, maximo=0.12, el_min=-25.0):
    """Radio de la BASE del pelo por dirección (H.D) para que la superficie exterior (base + mechones de `espesor`)
    llegue al casco de la hoja. Solo en el área de pelo y sobre `el_min`; acotado alrededor del radio original."""
    Rr, _ = casco(c, H.D, ref, al, r0=float(H.Rd.min()) * 0.6, r1=r1)
    el = np.degrees(np.arcsin(np.clip(H.D[:, 1], -1, 1)))
    obj = np.clip(Rr - espesor, H.Rd + minimo, H.Rd + maximo)
    peso = np.clip((el - el_min) / 15.0, 0, 1) * np.clip((H.Md - 0.75) / 0.25, 0, 1) ** 2   # la orilla queda pegada a la piel
    return H.Rd + (obj - H.Rd) * peso, Rr
