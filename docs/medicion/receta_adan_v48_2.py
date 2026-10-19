"""Adán V48.2 (sobre V47): sin el "rollo" del pelo en la nuca y sin la "visera" sobre los ojos.

Admin (19 oct 2026), con capturas de V47: "¿Ves los bultos en nuca y cejas que me refiero?"
- Nuca: el pelo se enrollaba ~3.5 cm hacia adentro bajo la altura de la oreja. Ahora el plano de atrás baja recto, y la
  piel de abajo se mueve lo mismo (bultos_cabeza.nuca_recta).
- Cejas: la piel sobre los ojos sobresalía ~2.5 mm. Ahora la frente baja recta hasta los párpados (bultos_cabeza.frente_recta);
  las cejas se desplazan con la piel, sin cambiar de forma.
La forma general, cachetes, ojos, boca, nariz y orejas quedan como V47. Al final se vuelve a sellar el borde del pelo
de la nuca sobre la piel (pelo_nuca).
Uso: python receta_adan_v48_2.py ADAN_V47.glb ADAN_V48_2.glb
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v39 as v39  # noqa: E402
import receta_adan_v48 as v48  # noqa: E402

PELO = ("GUIA_CAPILAR_RELLENO_RUBIO_v04", "GUIA_CAPILAR_CONTORNO_RUBIO_v04")
PIEL = "Cabeza_PIEL_EXPUESTA_v04"
NUCA_SELLO = dict(delta=0.004, banda=0.016, ancho_th=95.0, holgura=0.0015)


def _escribir(E, p, V0, V1):
    from copox.medicion.gltf import accesor
    mov = np.abs(V1 - V0).max(1) > 1e-7
    if not mov.any():
        return 0
    p["attributes"]["POSITION"] = E._add(V1.astype(np.float32), "VEC3", 34962, True)
    if "NORMAL" in p["attributes"]:
        T = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        N0 = v39._leer(E, p, "NORMAL").astype(float)
        N1 = v48._normales_soldadas(V1, T)
        if np.einsum("ij,ij->i", N0, N1).mean() < 0:
            N1 = -N1
        N = N0.copy(); N[mov] = N1[mov]
        p["attributes"]["NORMAL"] = E._add(N.astype(np.float32), "VEC3", 34962)
    E.b = bytes(E.out)                                   # lo escrito se puede volver a leer
    return int(mov.sum())


def bultos(E):
    from scipy.interpolate import LinearNDInterpolator
    from copox.medicion import bultos_cabeza as bc
    mat = {i: m["name"] for i, m in enumerate(E.j["materials"])}
    prims = {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}
    log = {"operacion": "bultos de la cabeza"}
    # 1. nuca: pelo y piel con el mismo desplazamiento
    Vh = v39._leer(E, prims[PELO[0]], "POSITION").astype(float)
    fn = bc.nuca_recta(Vh)
    for pz in PELO + (PIEL,):
        V = v39._leer(E, prims[pz], "POSITION").astype(float)
        V1, d = fn(V)
        log[f"nuca_{pz[:12]}"] = {"movidos": _escribir(E, prims[pz], V, V1), "max_mm": round(float(d.max()) * 1000, 1)}
    # 2. frente: la piel directo; cejas y demás piezas de la cara con el desplazamiento de la piel en su (x, y)
    p = prims[PIEL]
    S = v39._leer(E, p, "POSITION").astype(float)
    S1 = bc.frente_recta(S)(S)
    dz = S1[:, 2] - S[:, 2]
    m = np.abs(dz) > 1e-7
    log["frente_piel"] = {"movidos": _escribir(E, p, S, S1), "max_mm": round(float(-dz.min()) * 1000, 2)}
    if m.any():
        D = LinearNDInterpolator(S[m][:, :2], dz[m], fill_value=0.0)
        n = 0
        for mm in E.j["meshes"]:
            for q in mm["primitives"]:
                nombre = mat[q["material"]]
                pz = q.get("extras", {}).get("pieza") or ""
                if q is p or pz.startswith(("PARPADO", "Ojo", "BORDE")) or not ("CEJA" in nombre or "PIEL" in nombre):
                    continue
                V = v39._leer(E, q, "POSITION").astype(float)
                cerca = (V[:, 2] > 0.06) & (np.abs(V[:, 0]) < 0.14) & (V[:, 1] > 0.64) & (V[:, 1] < 0.75)
                if not cerca.any():
                    continue
                V1 = V.copy(); V1[cerca, 2] += D(V[cerca, :2])
                n += _escribir(E, q, V, V1)
        log["frente_otras_piezas"] = n
    E.b = bytes(E.out)
    return log


def alisar_pelo(E, iter_=12):
    """Alisado (Taubin, sin encoger) solo de la franja baja de atrás de las dos capas del pelo, con el borde fijo."""
    from copox.medicion.gltf import accesor
    from copox.medicion.mano_geo import taubin
    prims = {p.get("extras", {}).get("pieza"): p for m in E.j["meshes"] for p in m["primitives"]}
    log = {"operacion": "alisar franja del pelo"}
    for pz in PELO:
        p = prims[pz]
        V = v39._leer(E, p, "POSITION").astype(float)
        T = accesor(E.j, E.b, p["indices"]).reshape(-1, 3).astype(np.int64)
        _, inv = np.unique(np.round(V, 6), axis=0, return_inverse=True); inv = inv.ravel()
        Vw = np.zeros((inv.max() + 1, 3)); Vw[inv] = V
        Tw = inv[T]
        e = np.sort(np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
        u, c = np.unique(e, axis=0, return_counts=True)
        borde = np.zeros(len(Vw), bool); borde[np.unique(u[c == 1])] = True
        S = taubin(Vw, Tw, iter_)
        y, z = Vw[:, 1], Vw[:, 2]
        w = np.clip((0.635 - y) / 0.03, 0, 1) * np.clip((-0.02 - z) / 0.03, 0, 1) * ~borde
        w = w * w * (3 - 2 * w)
        Vn = Vw + (S - Vw) * w[:, None]
        V1 = Vn[inv]
        log[pz[:20]] = _escribir(E, p, V, V1)
    return log


def sello(E):
    import receta_adan_v45 as v45
    n0 = dict(v45.NUCA)
    v45.NUCA.clear(); v45.NUCA.update(NUCA_SELLO)
    try:
        return v45.nuca(E)
    finally:
        v45.NUCA.clear(); v45.NUCA.update(n0)


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [bultos(E), alisar_pelo(E)]          # sin resellar: pelo y piel ya se movieron juntos
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V48.2: sin rollo en la nuca ni visera sobre los ojos. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
