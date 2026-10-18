"""COPOX · mano de una pieza (palma + dedos + pulgar con membranas) para rigs tipo Adán.

Se arma como superficie implícita (distancia con signo) alrededor de los huesos en reposo:
  palma = caja redondeada que se angosta hacia la muñeca; dedos y pulgar = cápsulas cónicas por falange;
  eminencia tenar = elipsoide en la base del pulgar. Palma ∪ dedos con unión suave (smin): la unión crea las
  membranas en "U" entre los dedos y el nudillo redondeado, sin piezas metidas una en otra.
Se poligoniza con marching cubes (scikit-image, BSD) y se pule con Taubin. Pesos por cadena de huesos con rampas
suaves en cada articulación (misma regla que la receta V27), suavizados sobre la malla. Todo lado izquierdo; el
derecho es espejo en x (el rig es simétrico).
"""
from __future__ import annotations
import numpy as np


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _capsula(P, a, b, r1, r2):
    ab = b - a; L2 = max(float(ab @ ab), 1e-12)
    t = np.clip((P - a) @ ab / L2, 0, 1)
    q = a + t[:, None] * ab
    return np.linalg.norm(P - q, axis=1) - (r1 + (r2 - r1) * t)


def _caja_red(P, c, h, r):
    q = np.abs(P - c) - (h - r)
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - r


def _elipsoide(P, c, rad):
    k0 = np.linalg.norm((P - c) / rad, axis=1)
    k1 = np.linalg.norm((P - c) / rad ** 2, axis=1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-12)


class Diseno:
    """Parámetros de la mano (izquierda, pose T, palma abajo, dedos hacia +x). Unidades del modelo."""
    def __init__(self, H, puntas, pulgar_punta, palma_x0, palma_y, palma_z, grosor, dedo_r, pulgar_r,
                 tenar, k_membrana, conico=0.85, angosta_muneca=0.82, radio_palma=0.009, angosta_pulgar=0.82):
        self.H, self.puntas, self.pulgar_punta = H, puntas, pulgar_punta
        self.palma_x0, self.palma_y, self.palma_z, self.grosor = palma_x0, palma_y, palma_z, grosor
        self.dedo_r, self.pulgar_r, self.tenar, self.k = dedo_r, pulgar_r, tenar, k_membrana
        self.conico, self.angosta, self.rp = conico, angosta_muneca, radio_palma
        self.angosta_pulgar = angosta_pulgar

    def cadenas(self):
        H = self.H
        out = {}
        for d in ("Index", "Middle", "Ring", "Little"):
            out[d] = [H["LeftHand"], H[f"Left{d}Proximal"], H[f"Left{d}Intermediate"], H[f"Left{d}Distal"], self.puntas[d]]
        out["Thumb"] = [H["LeftHand"], H["LeftThumbMetacarpal"], H["LeftThumbProximal"], H["LeftThumbDistal"], self.pulgar_punta]
        return out

    def sdf(self, P):
        H = self.H
        # palma: caja redondeada; en z se angosta hacia la muñeca (se escala z alrededor del centro)
        x1 = np.mean([H[f"Left{d}Proximal"][0] for d in ("Index", "Middle", "Ring", "Little")]) + 0.004
        cx = (self.palma_x0 + x1) / 2; hx = (x1 - self.palma_x0) / 2
        cz = (self.palma_z[0] + self.palma_z[1]) / 2; hz = (self.palma_z[1] - self.palma_z[0]) / 2
        u = np.clip((P[:, 0] - self.palma_x0) / (x1 - self.palma_x0), 0, 1)
        su = u * u * (3 - 2 * u)
        esc = self.angosta + (1 - self.angosta) * su
        # lado del pulgar (+z): el borde va en diagonal de la muñeca al nudillo del índice (como la mano con
        # regla), así el pulgar sale de la palma en vez de quedar tapado
        esc_p = self.angosta_pulgar + (1 - self.angosta_pulgar) * su
        esc = np.where(P[:, 2] > cz, esc_p, esc)
        Q = P.copy(); Q[:, 2] = cz + (P[:, 2] - cz) / esc
        d = _caja_red(Q, np.array([cx, self.palma_y, cz]), np.array([hx, self.grosor / 2, hz]), self.rp)
        # tenar (base del pulgar)
        d = _smin(d, _elipsoide(P, self.tenar[0], self.tenar[1]), self.k)
        dedos = None                                # dedos entre sí: unión dura (no se pegan como mitón)
        for nombre, cad in self.cadenas().items():
            r0 = self.pulgar_r if nombre == "Thumb" else self.dedo_r[nombre]
            dd = None
            seg = cad[1:]
            for i in range(len(seg) - 1):
                a, b = seg[i], seg[i + 1]
                if i == 0 and nombre != "Thumb":
                    a = a - (b - a) / np.linalg.norm(b - a) * 0.006     # la falange entra un poco en la palma
                r1 = r0 * (1 - (1 - self.conico) * i / (len(seg) - 1))
                r2 = r0 * (1 - (1 - self.conico) * (i + 1) / (len(seg) - 1))
                c = _capsula(P, a, b, r1, r2)
                dd = c if dd is None else np.minimum(dd, c)
            dedos = dd if dedos is None else np.minimum(dedos, dd)
        d = _smin(d, dedos, self.k)                 # solo palma ↔ dedos se funden: membranas y nudillos
        return d

    def malla(self, paso=0.0007, pulido=8):
        from skimage.measure import marching_cubes
        pts = np.vstack([np.array(list(self.H.values())), np.array(list(self.puntas.values())), self.pulgar_punta[None]])
        lo = np.array([self.palma_x0 - 0.006, pts[:, 1].min() - 0.03, min(self.palma_z[0], pts[:, 2].min()) - 0.02])
        hi = np.array([pts[:, 0].max() + 0.02, pts[:, 1].max() + 0.03, max(self.palma_z[1], pts[:, 2].max()) + 0.02])
        lo[0] = self.palma_x0 - 0.001
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.empty(n, np.float32)
        for ix in range(n[0]):                     # por rebanadas: poca memoria
            gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            F[ix] = self.sdf(g).reshape(n[1], n[2])
        # la palma queda abierta hacia la muñeca (se mete en el puño del antebrazo, como la pieza original)
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        T = T[:, ::-1].copy()                       # caras hacia afuera
        V = taubin(V, T, pulido)
        return V, T


def aristas(T, n):
    E = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
    import scipy.sparse as sp
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1
    return A


def taubin(V, T, it, lam=0.5, mu=-0.53):
    A = aristas(T, len(V)); deg = np.asarray(A.sum(1)).ravel()
    V = V.copy()
    for _ in range(it):
        for f in (lam, mu):
            V += f * (np.asarray(A @ V) / np.maximum(deg, 1)[:, None] - V)
    return V


def normales(V, T):
    Nf = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], Nf)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def pesos(V, T, D: Diseno, nombres_skin, pesos_cadena, anchos_dedo=(0.008, 0.006, 0.005),
          ancho_muneca=0.012, suavizado=6):
    """Pesos por cadena: cada vértice va a la cadena (dedo o pulgar) más cercana si está más allá de su nudillo;
    si no, a la palma (antebrazo → mano). Luego se suavizan sobre la malla y se dejan 4 por vértice."""
    H = D.H
    idx = {n: i for i, n in enumerate(nombres_skin)}
    W = np.zeros((len(V), len(nombres_skin)))
    # palma
    Wp = pesos_cadena(V, np.array([H["LeftLowerArm"], H["LeftHand"]]), D.puntas["Middle"], [ancho_muneca])
    asign = np.full(len(V), -1)
    mejor = np.full(len(V), np.inf)
    a_nud = np.full(len(V), -1.0)              # distancia al nudillo a lo largo del dedo asignado
    cads = D.cadenas()
    for k, (nombre, cad) in enumerate(cads.items()):
        r0 = D.pulgar_r if nombre == "Thumb" else D.dedo_r[nombre]
        seg = cad[1:]
        dmin = np.full(len(V), np.inf)
        for i in range(len(seg) - 1):
            dmin = np.minimum(dmin, _capsula(V, seg[i], seg[i + 1], 0, 0))
        # más allá del nudillo (proyección sobre la dirección de la primera falange). Cerca del nudillo (la
        # membrana entre dedos) solo cuenta lo que está sobre el dedo mismo; lo de en medio es palma (hueso Hand)
        u = seg[1] - seg[0]; u /= np.linalg.norm(u)
        a = (V - seg[0]) @ u
        lim = np.where(a < 0.010, r0 * 1.12, r0 * (1.25 if nombre == "Thumb" else 1.4))
        cerca = (a > -0.006) & (dmin < lim) & (dmin < mejor)
        asign[cerca] = k; mejor[cerca] = dmin[cerca]; a_nud[cerca] = a[cerca]
    for k, (nombre, cad) in enumerate(cads.items()):
        m = asign == k
        if not m.any():
            continue
        huesos = ["LeftHand", f"Left{nombre}{'Metacarpal' if nombre == 'Thumb' else 'Proximal'}",
                  f"Left{nombre}{'Proximal' if nombre == 'Thumb' else 'Intermediate'}", f"Left{nombre}Distal"]
        seglen = [float(np.linalg.norm(cad[i + 1] - cad[i])) for i in range(1, 4)]
        anchos = [min(anchos_dedo[i], 0.35 * seglen[i]) for i in range(3)]     # dedos cortos: rampas cortas
        Wc = pesos_cadena(V[m], np.array(cad[:4]), cad[4], anchos)
        for c, h in enumerate(huesos):
            W[m, idx[h]] = Wc[:, c]
    m = asign < 0
    W[m, idx["LeftLowerArm"]] = Wp[m, 0]; W[m, idx["LeftHand"]] = Wp[m, 1]
    # suavizado sin mezclar un dedo con otro: solo vecinos del mismo dedo, o dedo ↔ palma
    import scipy.sparse as sp
    A = aristas(T, len(V)).tocoo()
    ok = (asign[A.row] == asign[A.col]) | (asign[A.row] < 0) | (asign[A.col] < 0)
    A = sp.coo_matrix((np.ones(int(ok.sum())), (A.row[ok], A.col[ok])), shape=A.shape).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    es_pulgar = asign == list(cads).index("Thumb")
    banda = ((asign < 0) | (a_nud < 0.012) | (es_pulgar & (a_nud < 0.024)))[:, None]   # palma, nudillos y base del pulgar
    for _ in range(suavizado):
        W = np.where(banda, 0.5 * W + 0.5 * np.asarray(A @ W) / np.maximum(deg, 1)[:, None], W)
    orden = np.argsort(-W, axis=1)[:, :4]
    J4 = orden.astype(np.uint16)
    W4 = np.take_along_axis(W, orden, 1)
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-9)
    return J4, W4.astype(np.float32)


def espejo(V, T, N, J4, nombres_skin):
    """Lado derecho: x → −x, caras invertidas, huesos Left → Right."""
    idx = {n: i for i, n in enumerate(nombres_skin)}
    mapa = np.array([idx.get(n.replace("Left", "Right"), i) if n.startswith("Left") else i for i, n in enumerate(nombres_skin)])
    V2 = V * [-1, 1, 1]; N2 = N * [-1, 1, 1]
    return V2, T[:, ::-1].copy(), N2, mapa[J4].astype(np.uint16)
