"""SENKU · orejas: medidas de la oreja en unidades del ojo, comparables entre modelo y referencia.

Referencia ALTH (medida a mano sobre la Hoja de vistas, vista de perfil, 1254 px; ojo = 49 px de alto):
  oreja alto  = 68 px  → 1.39 ojos
  oreja ancho = 49 px  → 0.72 del alto (rectángulo vertical con esquinas redondeadas y bisel suave)
  arriba de la oreja: 11 px bajo el borde de arriba del ojo (0.22 ojos); abajo: a la altura de la boca
  hueco (concha) = 13 × 31 px → 0.27 del ancho × 0.46 del alto, centrado en alto, corrido hacia la cara
  de frente sobresale ≈ 8 % del ancho de la cabeza; de perfil su borde de enfrente queda 2.7 ojos detrás de la nariz
"""
from __future__ import annotations

import numpy as np

REF = {
    "alto_ojos": 1.39,
    "ancho_sobre_alto": 0.72,
    "arriba_bajo_ojo": 0.22,
    "hueco_ancho": 0.27,
    "hueco_alto": 0.46,
    "sobresale_cabeza": 0.08,
}


def medir(modelo, mat_ojo="C7V2_eye_BAKE_L", lado=1, piel_cabeza_min=5000, oreja=None):
    """Mide la oreja del lado +x (lado=1) en reposo. oreja: índices de primitivas de la oreja
    (por omisión, las de piel cuyo centro está a |x| > 0.12 y a la altura de la cara)."""
    P = modelo.posar(None)
    prims = modelo.prims
    ojo = next(k for k, p in enumerate(prims) if p.material.get("name") == mat_ojo)
    # el ojo visible: la placa con alfa (sin la parte transparente de arriba)
    po = prims[ojo]
    vis = po.uv[:, 1] > 0.08 if po.uv is not None else np.ones(len(po.pos), bool)
    ojo_alto = float(np.ptp(P[ojo][vis][:, 1]))
    ojo_arriba = float(P[ojo][vis][:, 1].max())
    piel = max((k for k, p in enumerate(prims) if len(p.pos) > piel_cabeza_min and p.joints is not None),
               key=lambda k: P[k][:, 1].max())
    cab = P[piel]
    if oreja is None:
        oreja = [k for k, p in enumerate(prims)
                 if p.material.get("name", "").startswith("PIEL") and k != piel and len(p.pos) < 5000
                 and lado * P[k][:, 0].mean() > 0.12 and abs(P[k][:, 1].mean() - ojo_arriba + 0.05) < 0.08
                 and np.ptp(P[k], axis=0).max() > 0.01]
    O = np.concatenate([P[k] for k in oreja])
    alto = float(np.ptp(O[:, 1])); ancho = float(np.ptp(O[:, 2]))
    cab_ancho = float(np.ptp(cab[:, 0]))
    sobresale = float(lado * O[:, 0].max() - cab[:, 0].max() * (lado > 0) + cab[:, 0].min() * (lado < 0))
    return {
        "alto_ojos": alto / ojo_alto,
        "ancho_sobre_alto": ancho / alto,
        "arriba_bajo_ojo": (ojo_arriba - O[:, 1].max()) / ojo_alto,
        "sobresale_cabeza": sobresale / cab_ancho,
        "alto": alto, "ancho": ancho, "ojo_alto": ojo_alto, "primitivas": oreja,
    }


def tabla(m: dict) -> str:
    filas = ["| Medida | Modelo | Referencia | Razón |", "|---|---|---|---|"]
    for k, r in REF.items():
        if k in m:
            filas.append(f"| {k} | {m[k]:.2f} | {r:.2f} | {m[k] / r:.2f} |")
    return "\n".join(filas)
