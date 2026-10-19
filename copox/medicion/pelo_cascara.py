"""SENKU · cáscara del pelo limpia (Adán V48.3).

Admin no aprobó V48.2: la "terraza" horizontal de la parte baja del pelo seguía, y se veía más grumosa. Esa banda está
construida en la malla vieja; empujarla o alisarla localmente la reacomoda pero no la quita. Por eso aquí la cáscara se
rehace como una sola superficie:
- Envolvente radial: desde el centro de la cabeza, para cada dirección (azimut, elevación), el radio máximo de la
  cáscara vieja. Se suaviza fuerte (gaussiana en la esfera): desaparecen la terraza, las ondas y las motas, y se
  conserva la silueta grande (la de V47, que Admin no objeta).
- Piso: en cada dirección el radio nunca baja de la piel + `holgura`, para que la piel no atraviese el pelo.
- La malla vieja (su topología y su orilla) se conserva: cada vértice solo cambia de radio. Las dos capas (RELLENO y
  CONTORNO) usan el mismo radio; CONTORNO, el del nacimiento del pelo, queda `sobre` mm por encima.
Pelo liso, como pidió Admin ("me sirve así"): el pelo final va al último.
"""
from __future__ import annotations

import numpy as np


def _esf(P, c):
    Q = P - c
    r = np.linalg.norm(Q, axis=1)
    az = np.arctan2(Q[:, 0], Q[:, 2])
    el = np.arcsin(np.clip(Q[:, 1] / np.maximum(r, 1e-12), -1, 1))
    return az, el, r


class Envolvente:
    def __init__(self, centro, puntos, nb=(144, 72), sigma=2.5, modo="max"):
        from scipy.ndimage import gaussian_filter, maximum_filter
        self.c = np.asarray(centro, float)
        na, ne = nb
        az, el, r = _esf(puntos, self.c)
        ia = np.clip(((az + np.pi) / (2 * np.pi) * na).astype(int), 0, na - 1)
        ie = np.clip(((el + np.pi / 2) / np.pi * ne).astype(int), 0, ne - 1)
        G = np.zeros((na, ne))
        np.maximum.at(G, (ia, ie), r)
        for _ in range(40):                                   # huecos: el máximo de los vecinos
            vacio = G == 0
            if not vacio.any():
                break
            M = maximum_filter(np.pad(G, ((2, 2), (1, 1)), mode="wrap"), size=3)[2:-2, 1:-1]
            G[vacio] = M[vacio]
        Gp = np.pad(G, ((3 * int(sigma) + 3,) * 2, (0, 0)), mode="wrap")
        G = gaussian_filter(Gp, sigma=(sigma, sigma), mode=("wrap", "nearest"))[3 * int(sigma) + 3:-(3 * int(sigma) + 3)]
        self.G = G
        self.az_c = (np.arange(na) + 0.5) / na * 2 * np.pi - np.pi
        self.el_c = (np.arange(ne) + 0.5) / ne * np.pi - np.pi / 2

    def R(self, P):
        from scipy.interpolate import RegularGridInterpolator
        az, el, _ = _esf(P, self.c)
        azp = np.r_[self.az_c[-1] - 2 * np.pi, self.az_c, self.az_c[0] + 2 * np.pi]
        Gp = np.vstack([self.G[-1:], self.G, self.G[:1]])
        f = RegularGridInterpolator((azp, self.el_c), Gp, bounds_error=False, fill_value=None)
        return f(np.c_[az, np.clip(el, self.el_c[0], self.el_c[-1])])


def rehacer(relleno, contorno, piel, centro, iter_=150, holgura=0.004, T=None, **_):
    """V48.3 (2.º intento). La envolvente por dirección inflaba la nuca: desde el centro, la orilla enrollada queda
    "lejos" y el máximo la arrastraba. Aquí se suaviza SOLO el radio de cada vértice sobre la propia malla del pelo
    (promedio con sus vecinos, `iter_` pasadas), con la orilla fija: la terraza, una arruga radial, desaparece y la
    forma grande no cambia. CONTORNO toma la misma razón de radio que su vértice más cercano de RELLENO. Piso: piel +
    `holgura`. T: triángulos de RELLENO."""
    from scipy.spatial import cKDTree
    c = np.asarray(centro, float)
    _, inv = np.unique(np.round(relleno, 6), axis=0, return_inverse=True); inv = inv.ravel()
    n = inv.max() + 1
    W = np.zeros((n, 3)); W[inv] = relleno
    Tw = inv[T]
    e = np.sort(np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    borde = np.zeros(n, bool); borde[np.unique(u[cnt == 1])] = True
    E = np.unique(e, axis=0)
    deg = np.bincount(E.ravel(), minlength=n).astype(float)
    Q = W - c
    r0 = np.linalg.norm(Q, axis=1); d = Q / np.maximum(r0, 1e-12)[:, None]
    r = r0.copy()
    for _ in range(iter_):
        s_ = np.zeros(n); np.add.at(s_, E[:, 0], r[E[:, 1]]); np.add.at(s_, E[:, 1], r[E[:, 0]])
        rn = 0.5 * r + 0.5 * s_ / np.maximum(deg, 1)
        r = np.where(borde, r0, rn)
    # sin piso: la piel de abajo, que no se ve, se mete donde haga falta (meter_piel)
    W1 = c + d * r[:, None]
    k = r / np.maximum(r0, 1e-12)
    R1 = W1[inv]
    # CONTORNO: misma razón que el vértice de RELLENO más cercano
    _, j = cKDTree(W).query(contorno)
    Qc = contorno - c
    C1 = c + Qc * k[j][:, None]
    return R1, C1


def meter_piel(piel, relleno_nuevo, centro, holgura=0.003, cono=0.012):
    """La piel escondida bajo el pelo se mete hasta quedar `holgura` por debajo de él, en cada dirección donde hay pelo
    (cono de ~0.7°). Afuera del pelo no se toca. Devuelve la piel nueva y cuántos vértices se movieron."""
    from scipy.spatial import cKDTree
    c = np.asarray(centro, float)
    Qh = relleno_nuevo - c; rh = np.linalg.norm(Qh, axis=1); dh = Qh / np.maximum(rh, 1e-12)[:, None]
    Qs = piel - c; rs = np.linalg.norm(Qs, axis=1); ds = Qs / np.maximum(rs, 1e-12)[:, None]
    vec = cKDTree(dh).query_ball_point(ds, r=cono)
    tope = np.array([rh[v].min() - holgura if len(v) else np.inf for v in vec])
    r2 = np.minimum(rs, tope)
    return c + ds * r2[:, None], int((r2 < rs - 1e-7).sum())


class PeloImplicito:
    """V48.3 (técnica nueva): el pelo es una cáscara implícita de grosor `grosor` sobre una superficie radial lisa
    R(dirección), recortada por la región del pelo viejo (máscara en la esfera, suavizada: orilla limpia).
    R sale del PROMEDIO de radios del pelo viejo por celda (no del máximo: la orilla enrollada inflaba la nuca), muy
    suavizado. La malla se genera nueva con marching cubes: sin el grano de la malla vieja."""

    def __init__(self, centro, pelo, nb=(144, 72), sigma=3.0, sigma_mask=2.0, grosor=0.004):
        from scipy.ndimage import gaussian_filter
        self.c = np.asarray(centro, float)
        na, ne = nb
        az, el, r = _esf(pelo, self.c)
        ia = np.clip(((az + np.pi) / (2 * np.pi) * na).astype(int), 0, na - 1)
        ie = np.clip(((el + np.pi / 2) / np.pi * ne).astype(int), 0, ne - 1)
        S = np.zeros((na, ne)); N = np.zeros((na, ne))
        np.add.at(S, (ia, ie), r); np.add.at(N, (ia, ie), 1)
        M = (N > 0).astype(float)
        pad = 3 * int(max(sigma, sigma_mask)) + 3
        f = lambda A, s: gaussian_filter(np.pad(A, ((pad, pad), (0, 0)), mode="wrap"), s, mode=("wrap", "nearest"))[pad:-pad]  # noqa: E731
        Rm = f(S, sigma) / np.maximum(f(N, sigma), 1e-9)                      # promedio normalizado
        self.R = Rm
        self.M = f(M, sigma_mask)
        self.grosor = grosor
        self.az_c = (np.arange(na) + 0.5) / na * 2 * np.pi - np.pi
        self.el_c = (np.arange(ne) + 0.5) / ne * np.pi - np.pi / 2
        self.paso_ang = 2 * np.pi / na

    def _interp(self, G, az, el):
        from scipy.interpolate import RegularGridInterpolator
        azp = np.r_[self.az_c[-1] - 2 * np.pi, self.az_c, self.az_c[0] + 2 * np.pi]
        Gp = np.vstack([G[-1:], G, G[:1]])
        f = RegularGridInterpolator((azp, self.el_c), Gp, bounds_error=False, fill_value=None)
        return f(np.c_[az, np.clip(el, self.el_c[0], self.el_c[-1])])

    def sdf(self, P):
        az, el, r = _esf(P, self.c)
        R = self._interp(self.R, az, el)
        M = self._interp(self.M, az, el)
        capa = np.abs(r - (R - self.grosor / 2)) - self.grosor / 2
        region = (0.5 - M) * R * self.paso_ang * 4                           # ~distancia angular a la orilla
        return np.maximum(capa, region)

    def malla(self, paso=0.0015, pulido=2):
        from skimage.measure import marching_cubes
        from .mano_geo import taubin
        rmax = float(self.R.max()) + 0.01
        lo = self.c - rmax; hi = self.c + rmax
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.empty(n, np.float32)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            F[ix] = self.sdf(g).reshape(n[1], n[2])
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        if pulido:
            V = taubin(V, T, pulido)
        return V, T

    def normales(self, V, h=0.0004):
        g = np.zeros_like(V)
        for i in range(3):
            d = np.zeros(3); d[i] = h
            g[:, i] = self.sdf(V + d) - self.sdf(V - d)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)


def _fibonacci(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1)


class PeloImplicitoEsfera(PeloImplicito):
    """Igual que PeloImplicito pero con R y la máscara sobre direcciones de Fibonacci (uniformes, sin polos): la rejilla
    en ángulos hundía la coronilla y dentaba la orilla. Máscara: proporción ponderada de pelo contra piel descubierta
    (piel que no tiene pelo encima) alrededor de cada dirección."""

    def __init__(self, centro, pelo, piel, n_dir=40000, sigma=0.05, sigma_mask=0.035, grosor=0.004):
        from scipy.spatial import cKDTree
        self.c = np.asarray(centro, float); self.grosor = grosor
        D = _fibonacci(n_dir)
        Qh = pelo - self.c; rh = np.linalg.norm(Qh, axis=1); dh = Qh / rh[:, None]
        Qs = piel - self.c; rs = np.linalg.norm(Qs, axis=1); ds = Qs / rs[:, None]
        th = cKDTree(dh)
        cubierta = np.array([len(v) > 0 for v in th.query_ball_point(ds, r=0.02)])
        ds = ds[~cubierta]
        R = np.zeros(n_dir); M = np.zeros(n_dir)
        for k in range(0, n_dir, 4000):
            q = D[k:k + 4000]
            vh = th.query_ball_point(q, r=3 * sigma)
            for i, v in enumerate(vh):
                if len(v):
                    a = np.arccos(np.clip(dh[v] @ q[i], -1, 1)); w = np.exp(-(a / sigma) ** 2)
                    R[k + i] = (w * rh[v]).sum() / w.sum()
        ts = cKDTree(ds)
        for k in range(0, n_dir, 4000):
            q = D[k:k + 4000]
            vh = th.query_ball_point(q, r=3 * sigma_mask); vs = ts.query_ball_point(q, r=3 * sigma_mask)
            for i in range(len(q)):
                wh = np.exp(-(np.arccos(np.clip(dh[vh[i]] @ q[i], -1, 1)) / sigma_mask) ** 2).sum() if len(vh[i]) else 0.0
                ws = np.exp(-(np.arccos(np.clip(ds[vs[i]] @ q[i], -1, 1)) / sigma_mask) ** 2).sum() if len(vs[i]) else 0.0
                M[k + i] = wh / (wh + ws) if wh + ws > 0 else 0.0
        # direcciones sin pelo cerca: radio del vecino con pelo más cercano (solo para que el campo sea continuo)
        sin = R == 0
        if sin.any():
            _, j = cKDTree(D[~sin]).query(D[sin]); R[sin] = R[~sin][j]
        self.D, self.Rd, self.Md = D, R, M
        self.arbol = cKDTree(D)
        self.paso_ang = 0.035

    def _campos(self, P):
        Q = P - self.c; r = np.linalg.norm(Q, axis=1); d = Q / np.maximum(r, 1e-12)[:, None]
        dist, j = self.arbol.query(d, k=6)
        w = 1.0 / np.maximum(dist, 1e-6) ** 2; w /= w.sum(1, keepdims=True)
        return r, (w * self.Rd[j]).sum(1), (w * self.Md[j]).sum(1)

    def sdf(self, P):
        r, R, M = self._campos(P)
        capa = np.abs(r - (R - self.grosor / 2)) - self.grosor / 2
        region = (0.5 - M) * R * self.paso_ang * 2.5
        return np.maximum(capa, region)

    def malla(self, paso=0.0015, pulido=2):
        from skimage.measure import marching_cubes
        from .mano_geo import taubin
        rmax = float(self.Rd.max()) + 0.01
        lo = self.c - rmax; hi = self.c + rmax
        n = np.ceil((hi - lo) / paso).astype(int) + 1
        ejes = [lo[i] + paso * np.arange(n[i]) for i in range(3)]
        F = np.full(n, 1.0, np.float32)
        gy, gz = np.meshgrid(ejes[1], ejes[2], indexing="ij")
        for ix in range(n[0]):
            g = np.stack([np.full(gy.size, ejes[0][ix]), gy.ravel(), gz.ravel()], 1)
            r = np.linalg.norm(g - self.c, axis=1)
            cerca = (r > self.Rd.min() - 0.02) & (r < rmax)            # banda estrecha: el resto queda afuera
            f = np.ones(len(g), np.float32)
            if cerca.any():
                f[cerca] = self.sdf(g[cerca])
            F[ix] = f.reshape(n[1], n[2])
        V, T, _, _ = marching_cubes(F, 0.0, spacing=(paso, paso, paso))
        V = V + lo
        vol = float(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum())
        if vol < 0:
            T = T[:, ::-1].copy()
        if pulido:
            V = taubin(V, T, pulido)
        return V, T


class PeloImplicitoRas(PeloImplicitoEsfera):
    """V48.3 c: la orilla baja hasta la piel (sin escalón ni canto). Afuera: radio de la piel + `ras` en la orilla, que
    sube suave hasta el radio del pelo hacia adentro (rampa en la máscara). Adentro: debajo de la piel."""

    def __init__(self, centro, pelo, piel, rampa=0.25, ras=0.0008, sigma_piel=0.03, **kw):
        from scipy.spatial import cKDTree
        super().__init__(centro, pelo, piel, **kw)
        Qs = piel - self.c; rs = np.linalg.norm(Qs, axis=1); ds = Qs / rs[:, None]
        ts = cKDTree(ds); Rs = np.zeros(len(self.D))
        for k in range(0, len(self.D), 4000):
            q = self.D[k:k + 4000]
            for i, v in enumerate(ts.query_ball_point(q, r=3 * sigma_piel)):
                if len(v):
                    w = np.exp(-(np.arccos(np.clip(ds[v] @ q[i], -1, 1)) / sigma_piel) ** 2)
                    Rs[k + i] = (w * rs[v]).sum() / w.sum()
        sin = Rs == 0
        if sin.any():
            _, j = cKDTree(self.D[~sin]).query(self.D[sin]); Rs[sin] = Rs[~sin][j]
        self.Rs, self.rampa, self.ras = Rs, rampa, ras

    def _campos2(self, P):
        Q = P - self.c; r = np.linalg.norm(Q, axis=1); d = Q / np.maximum(r, 1e-12)[:, None]
        dist, j = self.arbol.query(d, k=6)
        w = 1.0 / np.maximum(dist, 1e-6) ** 2; w /= w.sum(1, keepdims=True)
        f = lambda a: (w * a[j]).sum(1)                                           # noqa: E731
        return r, f(self.Rd), f(self.Md), f(self.Rs)

    def sdf(self, P):
        r, R, M, Rs = self._campos2(P)
        t = np.clip((M - 0.5) / self.rampa, 0, 1); t = t * t * (3 - 2 * t)
        fuera = np.maximum(Rs + self.ras + (R - Rs - self.ras) * t, Rs + self.ras)
        dentro = Rs - 0.004
        capa = np.maximum(r - fuera, dentro - r)
        region = (0.5 - M) * R * self.paso_ang * 2.5
        return np.maximum(capa, region)
