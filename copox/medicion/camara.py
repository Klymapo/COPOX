"""Cámara virtual para imitar la toma de una referencia.

Convención glTF: Y arriba, el personaje mira hacia +Z. yaw=0 es la vista de
frente; yaw=90 mira el costado izquierdo del personaje (cámara en +X);
yaw=180 la espalda. ``elevacion`` > 0 sube la cámara y mira hacia abajo.
``distancia`` None = ortográfica; si es un número (unidades del modelo) la
proyección es perspectiva con el objetivo en ``objetivo``.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class Camara:
    yaw: float = 0.0
    elevacion: float = 0.0
    roll: float = 0.0
    distancia: float | None = None
    objetivo: tuple = (0.0, 0.45, 0.0)

    def base(self):
        y, e = np.radians(self.yaw), np.radians(self.elevacion)
        hacia_cam = np.array([np.sin(y) * np.cos(e), np.sin(e), np.cos(y) * np.cos(e)])
        der = np.cross([0.0, 1.0, 0.0], hacia_cam)
        der /= np.linalg.norm(der)
        arriba = np.cross(hacia_cam, der)
        r = np.radians(self.roll)
        der, arriba = der * np.cos(r) + arriba * np.sin(r), -der * np.sin(r) + arriba * np.cos(r)
        return der, arriba, hacia_cam

    def proyectar(self, P: np.ndarray):
        """Devuelve (x, y, prof) en unidades del modelo sobre el plano del objetivo.
        x crece a la derecha de la imagen, y crece hacia ARRIBA; prof mayor = más cerca."""
        der, arriba, hc = self.base()
        Q = P - np.asarray(self.objetivo)
        x, y, z = Q @ der, Q @ arriba, Q @ hc
        if self.distancia is not None:
            f = self.distancia / np.maximum(self.distancia - z, 1e-6)
            x, y = x * f, y * f
        return x, y, z

    def dict(self):
        return asdict(self)
