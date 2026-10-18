"""SENKU · uniones: estiramiento y aplastamiento de aristas por pieza del cuerpo, en todos los clips.

python -m copox.movimiento.uniones MODELO.glb [--clips a,b] [--n 9]
Por clip: peor estiramiento (L/L0 máx) y peor aplastamiento (L/L0 mín) y en qué pieza (hueso dominante).
Meta de Admin: estiramiento < ×3 y sin aplastamientos < 0.25 (un pliegue que se cierra).
"""
from __future__ import annotations
import argparse, json
import numpy as np
from copox.medicion.gltf import Modelo


class Uniones:
    def __init__(self, glb):
        self.M = M = Modelo(glb)
        sk = M.j["skins"][0]["joints"]
        self.k = [k for k, p in enumerate(M.prims) if p.joints is not None and 30 < len(p.pos) < 5000 and np.ptp(p.pos, axis=0).max() > 0.005]
        rest = M.posar(None)
        self.E, self.L0, self.nombre = {}, {}, {}
        for k in self.k:
            p = M.prims[k]
            F = p.indices
            E = np.unique(np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
            L0 = np.linalg.norm(rest[k][E[:, 0]] - rest[k][E[:, 1]], axis=1)
            ok = L0 > 1e-6
            self.E[k], self.L0[k] = E[ok], L0[ok]
            dom = np.array(sk)[p.joints[np.arange(len(p.joints)), p.weights.argmax(1)]]
            u, c = np.unique(dom, return_counts=True)
            self.nombre[k] = M.j["nodes"][u[c.argmax()]]["name"] + f"#{k}"

    def clip(self, c, n=9):
        peor_e, peor_a = (1.0, "", 0), (1.0, "", 0)
        for f in np.linspace(0, 1, n):
            Ps = self.M.posar(c, f)
            for k in self.k:
                E = self.E[k]
                r = np.linalg.norm(Ps[k][E[:, 0]] - Ps[k][E[:, 1]], axis=1) / self.L0[k]
                if r.max() > peor_e[0]:
                    peor_e = (float(r.max()), self.nombre[k], round(float(f), 2))
                if r.min() < peor_a[0]:
                    peor_a = (float(r.min()), self.nombre[k], round(float(f), 2))
        return {"estira": round(peor_e[0], 2), "estira_en": peor_e[1], "aplasta": round(peor_a[0], 2), "aplasta_en": peor_a[1]}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("glb"); ap.add_argument("--clips", default=""); ap.add_argument("--n", type=int, default=9)
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    U = Uniones(a.glb)
    clips = [c for c in a.clips.split(",") if c] or [c for c in U.M.clips if not c.startswith(("G2", "V04")) and "Face" not in c and c not in ("Talk-loop", "Blink")]
    res = {}
    for c in clips:
        res[c] = r = U.clip(c, a.n)
        print(f"{c:24s} estira {r['estira']:5.2f} ({r['estira_en']:22s}) aplasta {r['aplasta']:4.2f} ({r['aplasta_en']})", flush=True)
    e = [r["estira"] for r in res.values()]; ap_ = [r["aplasta"] for r in res.values()]
    print(f"RESUMEN clips={len(res)} estira_max={max(e):.2f} clips_estira>3={sum(x > 3 for x in e)} aplasta_min={min(ap_):.2f} clips_aplasta<0.25={sum(x < 0.25 for x in ap_)}")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
