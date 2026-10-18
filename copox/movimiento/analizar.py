"""SENKU · movimiento: mide cada clip de un GLB riggeado, frame por frame.

Uso:  python -m copox.movimiento.analizar MODELO.glb salida.json [--fps 15]

Por clip reporta:
- actividad: grados máximos que gira cada hueso respecto al reposo (clip vacío si < 0.5°).
- estiramiento: razón largo de arista posada / reposo (p99.9 y máx, con el hueso dominante).
- mano_cabeza / mano_torso: vértices de mano dentro del volumen de la cabeza o del torso.
- piso: cuánto baja o sube el punto más bajo respecto al reposo (en % del alto).
"""
from __future__ import annotations
import json, sys, argparse
import numpy as np
from copox.medicion.gltf import Modelo, _q2m

MANO = ("Hand", "Index", "Middle", "Ring", "Little", "Thumb")
TORSO = ("Hips", "Spine", "Chest")


def _ang(q0, q1):
    d = abs(float(np.dot(q0, q1)) / (np.linalg.norm(q0) * np.linalg.norm(q1)))
    return float(np.degrees(2 * np.arccos(min(1.0, d))))


class Banco:
    def __init__(self, glb: str):
        self.M = M = Modelo(glb)
        j = M.j
        self.nombre = {i: n.get("name", str(i)) for i, n in enumerate(j["nodes"])}
        sk = j["skins"][0]["joints"]
        self.joints = sk
        # primitivas con skin del cuerpo
        self.ip = [k for k, p in enumerate(M.prims) if p.joints is not None]
        self.rest = M.posar(None)
        P = np.concatenate([self.rest[k] for k in self.ip])
        self.alto = float(P[:, 1].max() - P[:, 1].min())
        self.piso0 = float(P[:, 1].min())
        dom = []
        for k in self.ip:
            p = M.prims[k]
            dom.append(np.array(sk)[p.joints[np.arange(len(p.joints)), p.weights.argmax(1)]])
        self.dom = np.concatenate(dom)
        nom = np.array([self.nombre[d] for d in self.dom])
        self.es_mano = np.array([any(s in n for s in MANO) for n in nom])
        self.es_cabeza = nom == "Head"
        self.es_torso = np.isin(nom, TORSO)
        # aristas (índices globales)
        off, E = 0, []
        for k in self.ip:
            t = M.prims[k].indices + off
            E.append(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]))
            off += len(M.prims[k].pos)
        E = np.unique(np.sort(np.concatenate(E), 1), axis=0)
        L0 = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
        self.E, self.L0 = E[L0 > 1e-6], L0[L0 > 1e-6]
        self.idx = {self.nombre[i]: i for i in sk}
        # volúmenes en el marco del hueso (reposo)
        self.vol = {}
        for clave, mask, hueso in (("cabeza", self.es_cabeza, "Head"), ("torso", self.es_torso, "Chest")):
            Wb = M._mundo({})(self.idx[hueso])
            loc = (P[mask] - Wb[:3, 3]) @ Wb[:3, :3]
            c = (loc.max(0) + loc.min(0)) / 2
            r = (loc.max(0) - loc.min(0)) / 2
            self.vol[clave] = (hueso, c, r)
        self.base_pen = self._penetra(P, M._mundo({}))

    def _penetra(self, P, g):
        out = {}
        H = P[self.es_mano]
        for clave, (hueso, c, r) in self.vol.items():
            Wb = g(self.idx[hueso])
            loc = (H - Wb[:3, 3]) @ Wb[:3, :3]
            if clave == "cabeza":   # elipsoide al 90 %
                d = np.sqrt((((loc - c) / (r * 0.9)) ** 2).sum(1))
            else:                   # caja al 80 % (el torso es de caja)
                d = np.abs((loc - c) / (r * 0.8)).max(1)
            out[clave] = int((d < 1).sum())
        return out

    def clip(self, nombre: str, fps: float = 15) -> dict:
        M = self.M
        dur = M.duracion(nombre)
        n = max(2, int(round(dur * fps)) + 1)
        a = M.clips[nombre]
        # actividad por hueso
        act = {}
        for ch in a["channels"]:
            if ch["target"]["path"] != "rotation":
                continue
            node = ch["target"]["node"]
            q0 = M.j["nodes"][node].get("rotation", [0, 0, 0, 1])
            O = M._acc(a["samplers"][ch["sampler"]]["output"]).reshape(-1, 4)
            act[self.nombre[node]] = round(max(_ang(q0, q) for q in O), 2)
        pesos = [ch for ch in a["channels"] if ch["target"]["path"] == "weights"]
        morph_act = 0.0
        for ch in pesos:
            O = M._acc(a["samplers"][ch["sampler"]]["output"])
            morph_act = max(morph_act, float(np.abs(O).max()))
        est, peor, pen, piso = [], None, {"cabeza": 0, "torso": 0}, []
        pen_t = {"cabeza": None, "torso": None}
        for i in range(n):
            t = dur * i / (n - 1)
            trs, _ = M.muestrear(nombre, t)
            g = M._mundo(trs)
            Ps = M.posar(nombre, i / (n - 1))
            P = np.concatenate([Ps[k] for k in self.ip])
            L = np.linalg.norm(P[self.E[:, 0]] - P[self.E[:, 1]], axis=1) / self.L0
            dev = np.abs(np.log(L))
            k = int(dev.argmax())
            est.append(float(np.quantile(dev, 0.999)))
            if peor is None or dev[k] > peor[0]:
                peor = (float(dev[k]), round(t, 2), self.nombre[self.dom[self.E[k, 0]]])
            pp = self._penetra(P, g)
            for c in pen:
                extra = pp[c] - self.base_pen[c]
                if extra > pen[c]:
                    pen[c], pen_t[c] = extra, round(t, 2)
            piso.append(float(P[:, 1].min()) - self.piso0)
        vacio = (max(act.values(), default=0) < 0.5) and morph_act < 1e-3
        top = sorted(act.items(), key=lambda x: -x[1])[:5]
        return {
            "duracion": round(dur, 2), "frames": n, "vacio": vacio,
            "huesos_activos": sum(v >= 0.5 for v in act.values()),
            "top_huesos": top, "morph_max": round(morph_act, 3),
            "estira_p999": round(float(np.exp(max(est))), 3),
            "estira_max": round(float(np.exp(peor[0])), 3), "estira_max_t": peor[1], "estira_max_hueso": peor[2],
            "mano_en_cabeza": pen["cabeza"], "mano_en_cabeza_t": pen_t["cabeza"],
            "mano_en_torso": pen["torso"], "mano_en_torso_t": pen_t["torso"],
            "piso_min_pct": round(100 * min(piso) / self.alto, 2), "piso_max_pct": round(100 * max(piso) / self.alto, 2),
        }


def _acc(self, idx):
    from copox.medicion.gltf import accesor
    return accesor(self.j, self.b, idx).astype(float)


Modelo._acc = _acc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("glb"); ap.add_argument("salida"); ap.add_argument("--fps", type=float, default=15)
    ap.add_argument("--clips", default="")
    a = ap.parse_args(argv)
    b = Banco(a.glb)
    clips = [c for c in a.clips.split(",") if c] or list(b.M.clips)
    res = {"modelo": a.glb, "alto": b.alto, "base_penetracion": b.base_pen, "clips": {}}
    for c in clips:
        res["clips"][c] = r = b.clip(c, a.fps)
        print(f"{c:28s} vacio={r['vacio']!s:5} huesos={r['huesos_activos']:2d} estira={r['estira_max']:.2f}@{r['estira_max_hueso']} "
              f"cabeza={r['mano_en_cabeza']} torso={r['mano_en_torso']} piso={r['piso_min_pct']}..{r['piso_max_pct']}%", flush=True)
    json.dump(res, open(a.salida, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
