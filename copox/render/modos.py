"""Modos de vista calculados desde las capas por píxel (sin volver a rasterizar)."""
from __future__ import annotations

import numpy as np

from ..medicion import paleta

FONDO = np.array(paleta.COLORES[0], float) / 255


def a_lineal(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def a_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def muestrear(tex: np.ndarray, uv: np.ndarray, canal=None, bilineal=True):
    """Textura RGBA (h,w,4) en UV glTF (v hacia abajo, repetición)."""
    h, w = tex.shape[:2]
    u = (uv[:, 0] % 1.0) * w - 0.5
    v = (uv[:, 1] % 1.0) * h - 0.5
    if not bilineal:
        px = tex[np.clip(np.round(v), 0, h - 1).astype(int), np.clip(np.round(u), 0, w - 1).astype(int)]
        return px[:, canal] if canal is not None else px
    x0, y0 = np.floor(u).astype(int), np.floor(v).astype(int)
    fx, fy = (u - x0)[:, None], (v - y0)[:, None]
    x0c, x1c = np.clip(x0, 0, w - 1), np.clip(x0 + 1, 0, w - 1)
    y0c, y1c = np.clip(y0, 0, h - 1), np.clip(y0 + 1, 0, h - 1)
    t = tex if canal is None else tex[..., canal:canal + 1]
    px = (t[y0c, x0c] * (1 - fx) * (1 - fy) + t[y0c, x1c] * fx * (1 - fy)
          + t[y1c, x0c] * (1 - fx) * fy + t[y1c, x1c] * fx * fy)
    return px[:, 0] if canal is not None else px


class Capas:
    def __init__(self, ses, geo, cam, tri, tri_l, bary, prof, X, Y, Z, ss, esc, vista):
        self.ses, self.geo, self.cam, self.ss, self.esc, self.v = ses, geo, cam, ss, esc, vista
        self.tri, self.tri_l, self.bary, self.prof = tri, tri_l, bary, prof
        self.X, self.Y, self.Z = X, Y, Z
        self.fg = tri >= 0
        self.f = tri[self.fg]                      # cara por píxel de primer plano
        self.b = bary[self.fg].astype(float)       # baricéntricas en pantalla
        self.Fv = ses.F[self.f]                    # vértices por píxel
        if cam.distancia is not None:              # corrección de perspectiva
            dv = cam.distancia - Z[tri_l[self.fg]]
            bp = self.b / np.maximum(dv, 1e-9)
            self.bp = bp / bp.sum(1, keepdims=True)
        else:
            self.bp = self.b
        self._cache = {}

    def interp(self, A):
        return np.einsum("nk,nkd->nd", self.bp, A[self.Fv])

    def normal(self):
        if "N" not in self._cache:
            if self.v.sombreado == "archivo":  # normales del GLB, como las usa Godot
                N = self.interp(self.geo.Na)
            elif self.v.sombreado == "facetas":
                T = self.geo.P[self.Fv]
                N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            else:
                N = self.interp(self.geo.N)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
            hc = self.cam.base()[2]
            if self.cam.distancia is None:
                vis = np.broadcast_to(hc, N.shape)
            else:
                Pp = self.interp(self.geo.P)
                ojo = np.asarray(self.cam.objetivo) + hc * self.cam.distancia
                vis = ojo - Pp
                vis = vis / np.linalg.norm(vis, axis=1, keepdims=True)
            N = np.where(((N * vis).sum(1) < 0)[:, None], -N, N)  # cara trasera: voltear
            self._cache["N"] = N
        return self._cache["N"]

    def base(self):
        """Color base por píxel (sRGB 0-1), con textura muestreada por píxel."""
        if "base" not in self._cache:
            C = self.ses.rgbF[self.f].copy()
            pr = self.ses.prim[self.f]
            for k, tex in enumerate(self.ses.tex):
                if tex is None:
                    continue
                s = pr == k
                if s.any():
                    uv = np.einsum("nk,nkd->nd", self.bp[s], self.ses.UV[self.Fv[s]])
                    C[s] = muestrear(tex, uv)[:, :3]
            if self.ses.hay_vc:  # COLOR_0 multiplica el color base en espacio lineal (glTF)
                C = a_srgb(a_lineal(C) * self.interp(self.ses.VC))
            self._cache["base"] = C
        return self._cache["base"]

    def clases(self):
        C = np.zeros(self.tri.shape, np.uint8)
        if self.v.modo == "clases_tri":
            C[self.fg] = self.ses.claseF[self.f]
        else:
            C[self.fg] = paleta.clasificar(self.base() * 255)
        return C

    def oclusion(self):
        """Oclusión ambiental en pantalla a partir de la profundidad (0 = ocluido, 1 = libre).
        Se calcula a resolución de salida y se repite al supermuestreo."""
        k = self.ss
        fg = self.fg[::k, ::k]
        if not fg.any():
            return np.ones(self.tri.shape)
        zmin = self.prof[self.fg].min()
        zz = np.where(fg, self.prof[::k, ::k], zmin).astype(float)
        m = fg.astype(float)
        occ = np.zeros(fg.shape)
        esc = self.esc / k
        for r_u in (0.01, 0.025, 0.05):
            r = max(1, int(round(r_u * esc)))
            s, c = _caja(zz * m, r), _caja(m, r)
            occ += np.clip((s / np.maximum(c, 1e-9) - zz) / r_u, 0, 1)
        ao = 1 - 0.55 * np.clip(occ / 1.5, 0, 1)
        return np.repeat(np.repeat(ao, k, 0), k, 1)


def _caja(A, r):
    """Suma en ventana (2r+1)² con imagen integral."""
    H, W = A.shape
    I = np.zeros((H + 1, W + 1)); I[1:, 1:] = A.cumsum(0).cumsum(1)
    y0 = np.clip(np.arange(H) - r, 0, H); y1 = np.clip(np.arange(H) + r + 1, 0, H)
    x0 = np.clip(np.arange(W) - r, 0, W); x1 = np.clip(np.arange(W) + r + 1, 0, W)
    return I[y1][:, x1] - I[y0][:, x1] - I[y1][:, x0] + I[y0][:, x0]


def iluminar(cap: Capas, albedo_lineal: np.ndarray) -> np.ndarray:
    """Luz de estudio de 3 puntos + cielo/suelo, en espacio lineal."""
    der, arriba, hc = cap.cam.base()
    N = cap.normal()

    def d(v):
        v = np.asarray(v, float); return v / np.linalg.norm(v)
    clave = d(-0.45 * der + 0.55 * arriba + 0.70 * hc)
    relleno = d(0.65 * der + 0.10 * arriba + 0.75 * hc)
    contra = d(0.25 * der + 0.55 * arriba - 0.80 * hc)
    up = np.array([0.0, 1.0, 0.0])
    luz = (0.80 * np.clip(N @ clave, 0, 1) + 0.28 * np.clip(N @ relleno, 0, 1)
           + 0.30 * np.clip(N @ contra, 0, 1) + 0.30 + 0.12 * (N @ up))
    return albedo_lineal * luz[:, None]


def pintar(cap: Capas) -> np.ndarray:
    H, W = cap.tri.shape
    img = np.tile(FONDO, (H, W, 1))
    modo = cap.v.modo
    if modo in ("clases", "clases_tri"):
        return paleta.colorear(cap.clases())
    if not cap.fg.any():
        return (img * 255).astype(np.uint8)
    if modo == "normales":
        der, arriba, hc = cap.cam.base()
        N = cap.normal()
        img[cap.fg] = np.stack([N @ der, N @ arriba, N @ hc], 1) * 0.5 + 0.5
        return (img * 255).astype(np.uint8)
    ao = cap.oclusion()[cap.fg][:, None]
    if modo == "color":
        lin = iluminar(cap, a_lineal(cap.base())) * ao
        img[cap.fg] = a_srgb(lin)
    else:
        gris = iluminar(cap, np.full((cap.fg.sum(), 3), a_lineal(0.72))) * ao
        img[cap.fg] = a_srgb(gris)
        if modo == "curvatura":
            k = cap.interp(cap.geo.curv[:, None])[:, 0]
            esc = np.percentile(np.abs(k), 98) + 1e-12
            k = np.clip(k / esc, -1, 1)
            k = (np.sign(k) * np.abs(k) ** 0.7)[:, None]
            rojo, azul = np.array([0.85, 0.18, 0.12]), np.array([0.15, 0.35, 0.90])
            tinte = np.where(k > 0, rojo, azul)
            lum = img[cap.fg].mean(1, keepdims=True)
            img[cap.fg] = (1 - np.abs(k)) * img[cap.fg] + np.abs(k) * tinte * (0.45 + 0.75 * lum)
        elif modo == "malla":
            tl = cap.tri_l[cap.fg]
            Xs, Ys = cap.X[tl], cap.Y[tl]
            area2 = np.abs((Xs[:, 1] - Xs[:, 0]) * (Ys[:, 2] - Ys[:, 0]) - (Xs[:, 2] - Xs[:, 0]) * (Ys[:, 1] - Ys[:, 0]))
            dist = []
            for i, (a, b) in enumerate(((1, 2), (2, 0), (0, 1))):
                L = np.hypot(Xs[:, a] - Xs[:, b], Ys[:, a] - Ys[:, b])
                dist.append(cap.b[:, i] * area2 / np.maximum(L, 1e-9))
            dmin = np.min(dist, 0)
            a = np.clip(1.0 - (dmin - 0.35 * cap.ss) / (0.6 * cap.ss), 0, 1)[:, None] * 0.6
            img[cap.fg] = img[cap.fg] * (1 - a) + np.array([0.10, 0.12, 0.18]) * a
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def reducir(img: np.ndarray, ss: int) -> np.ndarray:
    H, W = img.shape[:2]
    return img.reshape(H // ss, ss, W // ss, ss, -1).mean((1, 3)).round().astype(np.uint8)


def _ruta_fuente():
    """DejaVu Sans (acentos y ñ): sistema o la copia que trae matplotlib; si no hay, la de Pillow."""
    import glob
    import os
    rutas = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    try:
        import matplotlib
        rutas.append(os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf/DejaVuSans.ttf"))
    except ImportError:
        pass
    rutas += glob.glob("/usr/share/fonts/**/DejaVuSans.ttf", recursive=True)
    return next((r for r in rutas if os.path.exists(r)), None)


_RUTA = _ruta_fuente()


def _fuente(tam):
    from PIL import ImageFont
    if _RUTA:
        return ImageFont.truetype(_RUTA, tam)
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:
        return ImageFont.load_default()


def sellar(img: np.ndarray, texto: str, codigo: str = "", t: int | None = None) -> np.ndarray:
    """Agrega una franja inferior con el sello (no tapa el modelo). t: tamaño de letra."""
    from PIL import Image, ImageDraw
    W = img.shape[1]
    t = t or max(11, min(W, img.shape[0]) // 46)
    fc = _fuente(max(9, int(t * 0.8)))
    lineas = []
    if codigo:  # el código se parte en renglones que quepan (nunca se corta)
        actual = ""
        for parte in codigo.split(";"):
            prueba = f"{actual};{parte}" if actual else parte
            if actual and fc.getlength(prueba) > W - 12:
                lineas.append(actual + ";"); actual = parte
            else:
                actual = prueba
        lineas.append(actual)
    paso = int(t * 1.5)
    alto = paso + int(t * 1.2) * len(lineas) + 8
    out = Image.new("RGB", (W, img.shape[0] + alto), (24, 26, 32))
    out.paste(Image.fromarray(img), (0, 0))
    d = ImageDraw.Draw(out)
    d.text((6, img.shape[0] + 3), texto, fill=(235, 235, 235), font=_fuente(t))
    for i, ln in enumerate(lineas):
        d.text((6, img.shape[0] + 3 + paso + i * int(t * 1.2)), ln, fill=(150, 160, 175), font=fc)
    return np.asarray(out)
