"""Sesión de render: el modelo queda cargado y las poses en caché.

    from copox.render import Sesion
    s = Sesion("THEO_V03.glb")
    r = s.render("cara_34;modo=arcilla", autor="elio")
    r.guardar("salida.png")          # imagen con sello
    r.clases                         # mapa de clases (paleta ALTH) para el motor de medición

Rasteriza una vez y calcula el modo pedido desde las capas por píxel.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import time
from dataclasses import dataclass, replace

import numpy as np

from ..medicion.camara import Camara
from ..medicion.gltf import Modelo
from ..medicion import paleta
from . import modos
from .raster import rasterizar
from .vistas import Vista, leer

_REGIONES = {"cara": ("Head",), "mano_izq": ("LeftHand",), "mano_der": ("RightHand",), "pies": ("LeftFoot", "RightFoot")}


@dataclass
class Geo:
    P: np.ndarray          # (V,3) posiciones posadas
    N: np.ndarray          # (V,3) normales suaves (soldadas por posición)
    curv: np.ndarray       # (V,) curvatura media aproximada (+ convexo)
    Na: np.ndarray = None  # (V,3) normales guardadas en el archivo (las que usa Godot)


@dataclass
class Resultado:
    imagen: np.ndarray     # (H,W,3) uint8 sin sello
    clases: np.ndarray     # (H,W) uint8
    prof: np.ndarray       # (H,W) profundidad (−inf fondo)
    tri: np.ndarray        # (H,W) triángulo (−1 fondo)
    vista: Vista
    escala: float          # px por unidad
    centro: tuple          # px del objetivo
    cam: Camara
    segundos: float
    sello: str
    codigo: str

    def con_sello(self) -> np.ndarray:
        return modos.sellar(self.imagen, self.sello, self.codigo)

    def guardar(self, ruta: str, sello: bool = True):
        from PIL import Image
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        img = self.con_sello() if sello else self.imagen
        Image.fromarray(img).save(ruta, optimize=True)
        return ruta


class Sesion:
    def __init__(self, glb: str, cull: bool = True):
        self.cull = cull
        t0 = time.time()
        self.ruta = glb
        self.nombre = os.path.splitext(os.path.basename(glb))[0]
        with open(glb, "rb") as fh:
            self.hash = hashlib.sha256(fh.read()).hexdigest()
        self.m = m = Modelo(glb)
        j = m.j
        F, prim, off = [], [], 0
        UV, rgbF, visF, dom, VC = [], [], [], [], []
        self.nodo_de_prim = []
        self.tex = []        # por primitiva: textura RGBA o None
        self.mask = []       # por primitiva: corte alfa o None
        self.doble = []      # por primitiva: material de dos caras
        self.mat_nombre = []
        nombres_j = {}
        for p in m.prims:
            n = j["nodes"][p.nodo]
            self.nodo_de_prim.append(n.get("name", ""))
            k = len(self.tex)
            F.append(p.indices + off); prim.append(np.full(len(p.indices), k, np.int32))
            UV.append(p.uv if p.uv is not None else np.zeros((len(p.pos), 2)))
            VC.append(p.color if p.color is not None else np.ones((len(p.pos), 3)))
            rgb, vis = m.color_triangulos(p)
            rgbF.append(rgb); visF.append(vis)
            self.tex.append(p.textura)
            self.mat_nombre.append(p.material.get("name", ""))
            self.doble.append(bool(p.material.get("doubleSided", False)))
            self.mask.append(p.material.get("alphaCutoff", 0.5) if p.material.get("alphaMode") == "MASK" and p.textura is not None else None)
            if "skin" in n and p.joints is not None:
                sk = j["skins"][n["skin"]]["joints"]
                dj = p.joints[np.arange(len(p.pos)), p.weights.argmax(1)]
                dom.append(np.array([sk[x] for x in dj], np.int64))
            else:
                dom.append(np.full(len(p.pos), -1, np.int64))
            off += len(p.pos)
        self.F = np.concatenate(F)
        self.prim = np.concatenate(prim)
        self.UV = np.concatenate(UV)
        self.VC = np.concatenate(VC)                      # color de vértice (lineal), 1 si no hay
        self.hay_vc = any(p.color is not None for p in m.prims)
        self.rgbF = np.concatenate(rgbF)
        self.visF = np.concatenate(visF)
        self.claseF = paleta.clasificar(self.rgbF * 255)
        self.dom = np.concatenate(dom)
        self.nodoF = np.array(self.nodo_de_prim)[self.prim]
        self._poses: dict = {}
        self._soldar = None
        self.carga_s = time.time() - t0

    # --- geometría -----------------------------------------------------------
    def _soldadura(self, P):
        if self._soldar is None:
            q = np.round(P / 1e-5).astype(np.int64)
            _, inv = np.unique(q, axis=0, return_inverse=True)
            self._soldar = inv.reshape(-1)
        return self._soldar

    def geo(self, clip: str | None, t: float) -> Geo:
        clave = (clip, round(t, 6))
        if clave not in self._poses:
            if clip in (None, "reposo"):
                clip = None
            elif clip not in self.m.clips:
                raise KeyError(f"Clip desconocido: {clip}")
            Pl, Nl = self.m.posar(clip, t, normales=True)
            P, Na = np.concatenate(Pl), np.concatenate(Nl)
            # soldadura en reposo (estable entre poses)
            w = self._soldadura(np.concatenate([p.pos for p in self.m.prims]))
            nw = w.max() + 1
            Fw = w[self.F]
            Pw = np.zeros((nw, 3)); np.add.at(Pw, w, P)
            cnt = np.bincount(w, minlength=nw)[:, None]
            Pw /= np.maximum(cnt, 1)
            T = Pw[Fw]
            Nf = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            Nw = np.zeros((nw, 3))
            for i in range(3):
                np.add.at(Nw, Fw[:, i], Nf)
            Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)
            # curvatura: laplaciano uniforme proyectado en la normal / largo medio de arista²
            E = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]])
            E = np.unique(np.sort(E, 1), axis=0)
            S = np.zeros((nw, 3)); c = np.zeros(nw); L = np.zeros(nw)
            le = np.linalg.norm(Pw[E[:, 0]] - Pw[E[:, 1]], axis=1)
            for a, b in ((0, 1), (1, 0)):
                np.add.at(S, E[:, a], Pw[E[:, b]]); np.add.at(c, E[:, a], 1); np.add.at(L, E[:, a], le)
            c = np.maximum(c, 1)
            lap = S / c[:, None] - Pw
            curv = -(lap * Nw).sum(1) / np.maximum((L / c) ** 2, 1e-12)
            for _ in range(2):  # suavizado leve para quitar ruido de triangulación
                sc = np.zeros(nw)
                np.add.at(sc, E[:, 0], curv[E[:, 1]]); np.add.at(sc, E[:, 1], curv[E[:, 0]])
                curv = 0.5 * curv + 0.5 * sc / c
            self._poses[clave] = Geo(P, Nw[w], curv[w], Na)
            if len(self._poses) > 8:
                self._poses.pop(next(iter(self._poses)))
        return self._poses[clave]

    def ojos_3d(self, clip, t) -> list:
        """Centro de la caja de cada placa de ojo (materiales con 'eye' en el nombre), en mundo, ordenados por x."""
        geo = self.geo(None if clip == "reposo" or clip not in self.m.clips else clip, t)
        cs = []
        for k, n in enumerate(self.mat_nombre):
            if "eye" in n.lower():
                vid = np.unique(self.F[self.prim == k])
                Q = geo.P[vid]
                cs.append((Q.min(0) + Q.max(0)) / 2)
        return sorted(cs, key=lambda p: p[0])

    def _region(self, nombre: str) -> np.ndarray:
        if nombre == "cuerpo":
            return np.ones(len(self.dom), bool)
        j = self.m.j
        hijos = {i: n.get("children", []) for i, n in enumerate(j["nodes"])}
        sel = set()
        for raiz in _REGIONES[nombre]:
            pila = [next(i for i, n in enumerate(j["nodes"]) if n.get("name") == raiz)]
            while pila:
                k = pila.pop(); sel.add(k); pila.extend(hijos[k])
        return np.isin(self.dom, list(sel))

    # --- render --------------------------------------------------------------
    def encuadre(self, v: Vista, geo: Geo, visibles: np.ndarray):
        """Devuelve (cam, escala, centro) para el tamaño v.tam (sin supermuestreo)."""
        H = W = v.tam
        if v.enc != "auto":
            alto, cx, cy = (float(x) for x in v.enc.split(","))
            cam = Camara(v.yaw, v.elev, v.roll, v.dist, objetivo=(0.0, cy, 0.0))
            esc = H / alto
            return cam, esc, (W / 2 - cx * esc, H / 2)
        cam = Camara(v.yaw, v.elev, v.roll, v.dist)
        vid = np.unique(self.F[visibles])
        vid = vid[self._region(v.region)[vid]]
        if len(vid) == 0:
            raise ValueError(f"Región vacía: {v.region}")
        x, y, _ = cam.proyectar(geo.P[vid])
        w, h = x.max() - x.min(), y.max() - y.min()
        esc = min(W / (w * 1.16 + 1e-9), H / (h * 1.16 + 1e-9))
        xc, yc = (x.max() + x.min()) / 2, (y.max() + y.min()) / 2
        return cam, esc, (W / 2 - xc * esc, H / 2 + yc * esc)

    def render(self, vista: Vista | str, autor: str = "elio", fijar=None) -> Resultado:
        """fijar=(escala, centro) reutiliza el encuadre de otro render (A/B)."""
        t0 = time.time()
        v = leer(vista) if isinstance(vista, str) else replace(vista)
        clip = None if v.clip == "reposo" else (v.clip if v.clip in self.m.clips else None)
        geo = self.geo(clip, v.t)
        visibles = np.ones(len(self.F), bool)
        if v.ocultar:  # por nombre de nodo o de material
            visibles &= ~np.isin(self.nodoF, v.ocultar) & ~np.isin(np.array(self.mat_nombre)[self.prim], v.ocultar)
        if v.modo == "clases_tri":
            visibles &= self.visF
        cam, esc, cen = self.encuadre(v, geo, visibles)
        if fijar is not None:
            esc, cen = fijar
        ss = 1 if v.modo in ("clases", "clases_tri") else 2
        H = W = v.tam * ss
        if self.cull:
            # descarte de caras traseras, como Godot (salvo materiales doubleSided)
            T = geo.P[self.F]
            Nf = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            hc = cam.base()[2]
            if cam.distancia is None:
                frente = Nf @ hc > 0
            else:
                ojo = np.asarray(cam.objetivo) + hc * cam.distancia
                frente = (Nf * (ojo - T.mean(1))).sum(1) > 0
            visibles &= frente | np.array(self.doble)[self.prim]
        caras = np.nonzero(visibles)[0]
        T = geo.P[self.F[caras]]
        x, y, z = cam.proyectar(T.reshape(-1, 3))
        X = (cen[0] * ss + x * esc * ss).reshape(-1, 3)
        Y = (cen[1] * ss - y * esc * ss).reshape(-1, 3)
        Z = z.reshape(-1, 3)
        descartar = None
        if v.modo != "clases_tri" and any(m is not None for m in self.mask):
            descartar = self._descartar_alfa(caras)
        tri_l, bary, prof = rasterizar(X, Y, Z, (H, W), descartar)
        tri = np.where(tri_l >= 0, caras[np.maximum(tri_l, 0)], -1)
        capas = modos.Capas(self, geo, cam, tri, tri_l, bary, prof, X, Y, Z, ss, esc * ss, v)
        img = modos.pintar(capas)
        clases = capas.clases()
        if ss > 1:
            img = modos.reducir(img, ss)
            clases, prof, tri = clases[::ss, ::ss], prof[::ss, ::ss], tri[::ss, ::ss]
        v.nombre = v.nombre
        fecha = _dt.date.today().isoformat()
        sello = f"{self.nombre} · {self.hash[:8]} · {v.nombre} · {v.modo} · {v.tam}px · {autor} · {fecha}"
        return Resultado(img, clases, prof, tri, v, esc, cen, cam, time.time() - t0, sello, v.codigo())

    def _descartar_alfa(self, caras):
        mk = np.array([m is not None for m in self.mask])

        def f(tid, b0, b1, b2):
            fc = caras[tid]
            pr = self.prim[fc]
            out = np.zeros(len(tid), bool)
            for k in np.nonzero(mk)[0]:
                s = pr == k
                if not s.any():
                    continue
                Fi = self.F[fc[s]]
                uv = b0[s, None] * self.UV[Fi[:, 0]] + b1[s, None] * self.UV[Fi[:, 1]] + b2[s, None] * self.UV[Fi[:, 2]]
                a = modos.muestrear(self.tex[k], uv, canal=3)
                out[s] = a < self.mask[k]
            return out
        return f
