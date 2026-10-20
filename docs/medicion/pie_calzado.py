"""Pie con calzado paramétrico (V50): reemplaza los tenis de V49. Referencia: los zapatos de la hoja de Theo
(refs/personajes/joven-rubio-4-vistas.jpg). Brief: docs/investigacion/zapato.md (suela + vira, tacón, empeine,
punta, boca).

Cada calzado = SUELA (losa plana algo más ancha que el corte, con arco: el tacón queda como bloque) + CORTE (huella
superelíptica de punta cuadrada redondeada, empeine que sube hacia el tobillo, boca baja, orillas redondeadas) +
un surco de vira entre ambos. Presets: ZAPATO (Theo, negro de cuero) y TENIS (suela blanca alta, punta redonda).
El pie no existe dentro (pieza "pie con calzado"); PIES_DESCALZOS sigue como alternativa.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import receta_adan_v40 as v40  # noqa: E402
import receta_adan_v41 as v41  # noqa: E402
import receta_adan_v49 as v49  # noqa: E402

PRESETS = {
    # zapato de la hoja de Theo: suela gruesa y plana (≈1/4 del alto), sobresale un poco, tacón en bloque,
    # punta cuadrada de esquinas suaves, boca baja
    "ZAPATO": dict(holgura_x=0.008, holgura_z=0.010, suela=0.013, sobresale=0.0045, arco=0.0035, arco_z=(0.30, 0.62),
                   collar=0.068, punta_alto=0.036, sobre_pie=0.017, n=5.0, redondeo=0.006, vira=0.0015,
                   punta_cuadrada=0.6, panel=None, facetas=True,
                   colores=("#292929", "#1F1916"), nodo="PIES_ZAPATO", tris=1800),
    "TENIS": dict(holgura_x=0.008, holgura_z=0.010, suela=0.013, sobresale=0.0025, arco=0.0, arco_z=(0.3, 0.6),
                  collar=0.058, punta_alto=0.032, sobre_pie=0.007, n=3.0, redondeo=0.014, vira=0.0,
                  punta_cuadrada=0.15, panel=None, facetas=False, colores=("#A8453B", "#F7F0E7"), nodo="PIES_TENIS",
                  tris=2600),
}


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


class Calzado:
    def __init__(self, pie, p):
        self.p = p
        lo, hi = pie.min(0), pie.max(0)
        self.cx, self.cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        self.a = (hi[0] - lo[0]) / 2 + p["holgura_x"]
        self.b = (hi[2] - lo[2]) / 2 + p["holgura_z"]
        self.z0, self.z1 = self.cz - self.b, self.cz + self.b               # talón, punta (+z = adelante)
        zs = np.linspace(self.z0, self.z1, 40)
        h = np.array([pie[np.abs(pie[:, 2] - z) < 0.012, 1].max() if (np.abs(pie[:, 2] - z) < 0.012).any() else 0
                      for z in zs]) + p["sobre_pie"]
        h = np.clip(h, p["punta_alto"], p["collar"])
        h = np.convolve(np.r_[h[:5], h, h[-5:]], np.ones(11) / 11, mode="valid")
        self.zs, self.h = zs, h

    def _huella(self, P, extra=0.0):
        """Superelipse en planta; la punta (z alto) se cuadra un poco más que el talón."""
        p = self.p
        t = np.clip((P[:, 2] - self.z0) / (self.z1 - self.z0), 0, 1)
        n = p["n"] + 3.0 * p["punta_cuadrada"] * _ss((t - 0.55) / 0.35)
        a, b = self.a + extra, self.b + extra
        dx = np.abs(P[:, 0] - self.cx) / a; dz = np.abs(P[:, 2] - self.cz) / b
        k = (dx ** n + dz ** n) ** (1 / n)
        return (k - 1) * min(a, b)

    def suela(self, P):
        from copox.medicion.ropa_ajustada import smin
        p = self.p
        d = self._huella(P, p["sobresale"])
        d = np.maximum(d, np.maximum(P[:, 1] - p["suela"], -P[:, 1]))
        # arco: entre talón y planta la suela no toca el piso (el tacón queda como bloque)
        t = (P[:, 2] - self.z0) / (self.z1 - self.z0)
        en_arco = _ss((t - p["arco_z"][0]) / 0.05) * _ss((p["arco_z"][1] - t) / 0.05)
        d = np.maximum(d, (p["arco"] * en_arco) - P[:, 1])
        return d

    def corte(self, P):
        from copox.medicion.ropa_ajustada import smin
        p = self.p
        d2 = self._huella(P, -p["vira"])                                    # el corte entra un poco: se ve la vira
        top = np.interp(P[:, 2], self.zs, self.h)
        d = -smin(-d2, -(P[:, 1] - top), p["redondeo"])                     # empeine y orillas redondeadas
        if p.get("panel"):                                                  # panel de cordones hundido en el empeine
            prof, ancho, t0, t1 = p["panel"]
            t = (P[:, 2] - self.z0) / (self.z1 - self.z0)
            dentro = np.maximum(np.abs(P[:, 0] - self.cx) - ancho * self.a, np.maximum(t0 - t, t - t1) * (self.z1 - self.z0))
            d = np.maximum(d, -(P[:, 1] - (top - prof)) * (dentro < 0) - 1.0 * (dentro >= 0))
        return np.maximum(d, (p["suela"] - 0.002) - P[:, 1])                # arranca sobre la suela

    def sdf(self, P):
        return np.minimum(self.suela(P), self.corte(P))


def calzado(E, carpeta, preset="ZAPATO", visible=True):
    import receta_adan_v36 as v36
    from copox.medicion import mano_geo as mg
    from copox.medicion import ropa_ajustada as ra
    from copox.medicion import short_geo as sg
    p = PRESETS[preset]
    nombres, _ = v40.v38_skin(E)
    m_corte = v41._material(E, f"{preset}_CORTE", p["colores"][0])
    m_suela = v41._material(E, f"{preset}_SUELA", p["colores"][1])
    prims, log = [], {"operacion": f"calzado {preset}"}
    for lado, pz, pie_n in (("L", "PiernaL_PIEL", "PieL_PIEL"), ("R", "PiernaR_PIEL", "PieR_PIEL")):
        piezas = v49._prims(E)
        P = v49._pieza(E, pz)
        Vp = P.V0[P.V0[:, 1] < p["collar"]]
        if pie_n in piezas:                                   # desde V49 el pie vive aparte (PIES_DESCALZOS)
            Pp = v49._pieza(E, pie_n)
            Vp = np.vstack([Vp, Pp.V0])
        S = Calzado(Vp, p)
        lo = np.array([S.cx - S.a - 0.012, -0.004, S.z0 - 0.012])
        hi = np.array([S.cx + S.a + 0.012, p["collar"] + 0.01, S.z1 + 0.012])
        for parte, campo, mat in (("SUELA", S.suela, m_suela), ("CORTE", S.corte, m_corte)):
            V, T = sg.malla_sdf(campo, lo, hi, paso=0.0009, pulido=6)
            V, T = ra.solo_mayor(V, T)
            V, T = v36.simplificar(V, T, p["tris"] // 2, carpeta)
            N = v49._normales_sdf(campo, V)
            T = v49._orientar(V, T, N)
            J4, W4 = ra.pesos_por_piel_visible(V, [P], len(nombres))
            if p.get("facetas"):                                            # planos como los zapatos de la hoja
                J4, W4 = J4[T].reshape(-1, 4), W4[T].reshape(-1, 4)
                V, T, N = v49._facetado(V, T)
            else:
                N = mg.normales(V, T)
            prims.append(v41._prim_nueva(E, V, T, N, J4, W4, mat, f"{preset.title()}{lado}_{parte}"))
            log[f"{lado}_{parte}"] = int(len(T))
    v49._nodo(E, p["nodo"], prims, visible=visible)
    v49._limpiar(carpeta)
    return log


def zapatos(E, carpeta):
    """V50: fuera los tenis de V49; entran ZAPATO (visible) y TENIS rehechos con el mismo método (ocultos)."""
    viejos = [n for n in E.j["nodes"] if n.get("name") == "PIES_TENIS"]
    for n in viejos:
        n["name"] = "PIES_TENIS_V49"
        n["extensions"] = {"KHR_node_visibility": {"visible": False}}
    log = [calzado(E, carpeta, "ZAPATO", True), calzado(E, carpeta, "TENIS", False)]
    # los tenis de V49 se quitan del árbol (el nodo queda sin malla para no romper índices)
    for n in viejos:
        n.pop("mesh", None); n.pop("skin", None)
    return {"operacion": "zapatos", "partes": log}
