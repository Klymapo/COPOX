"""Pelo que se mueve (Admin, 19 oct 2026: "Que funcione como pelo. Que se mueva al correr o brincar").

Cada mechón recibe una cadena de 4 huesos hija de Head (Pelo_NN_0 en la raíz … Pelo_NN_3 en la punta). La piel del
mechón: la raíz queda en Head, y desde ahí pasa a su cadena con pesos suaves a lo largo del mechón. Las animaciones no
tocan estos huesos; el movimiento lo pone un resorte en el motor: Godot 4.4+ SpringBoneSimulator3D (gratis, nativo).
La configuración viaja en el GLB (extras del nodo del pelo → metadata "extras" en Godot) y la aplica
copox/godot/alth_resortes.gd, igual en el juego que en CHXP V2.
"""
from __future__ import annotations

import numpy as np

from .gltf import accesor

# medido en Godot 4.7 (puntas de mechón respecto a la cabeza, 60 fps): Idle ~7 mm, Run mediana 18 mm / p95 46 mm.
# Con rigidez 1.6 / gravedad 0.35 el pelo se caía 6 cm en reposo.
RESORTE = dict(rigidez=4.0, arrastre=0.6, gravedad=0.1, radio=0.006)       # unidades de Godot (m del GLB)
CENTROS = np.array([0.19, 0.55, 0.86])                                      # centro de cada hueso a lo largo de s


def _suave(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def agregar_cadenas(E, curvas, prefijo="Pelo", cabeza="Head"):
    """curvas: lista de arreglos (k, 3) con la línea central de cada mechón (raíz → punta, espacio de malla).
    Agrega 4 huesos por mechón al skin 0 (raíz, 0.38, 0.72, punta). -> (índices de joint por cadena, nombres)."""
    j = E.j
    sk = j["skins"][0]
    ih = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == cabeza)
    jh = sk["joints"].index(ih)
    IBM = accesor(j, E.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)   # columnas
    W_head = np.linalg.inv(IBM[jh])                       # mundo del Head en pose de reposo (malla en el origen)
    nuevos, cadenas, nombres = [], [], []
    for c, C in enumerate(curvas):
        idx = []
        padre, W_padre = ih, W_head
        for b in range(len(C)):
            p = np.append(C[b], 1.0)
            local = np.linalg.inv(W_padre) @ p
            nombre = f"{prefijo}_{c:02d}_{b}"
            j["nodes"].append({"name": nombre, "translation": [float(x) for x in local[:3]]})
            k = len(j["nodes"]) - 1
            j["nodes"][padre].setdefault("children", []).append(k)
            W = W_padre.copy(); W[:3, 3] = (W_padre @ np.append(local[:3], 1.0))[:3]
            sk["joints"].append(k)
            nuevos.append(np.linalg.inv(W))
            idx.append(len(sk["joints"]) - 1)
            nombres.append(nombre)
            padre, W_padre = k, W
        cadenas.append(idx)
    todo = np.concatenate([IBM, np.array(nuevos)]).transpose(0, 2, 1).reshape(-1, 16)
    sk["inverseBindMatrices"] = E._add(todo.astype(np.float32), "MAT4")
    E.b = bytes(E.out)
    return cadenas, jh


def pesos(ids, s, cadenas, j_cabeza, n_base=0):
    """Pesos por vértice: los primeros n_base vértices (base del cráneo) van a Head; cada vértice de mechón mezcla Head
    (raíz) con los 3 primeros huesos de su cadena (sombrero lineal entre CENTROS)."""
    n = n_base + len(ids)
    J = np.zeros((n, 4), np.uint16); W = np.zeros((n, 4), np.float32)
    J[:, 0] = j_cabeza; W[:n_base, 0] = 1
    h = 1 - _suave(s / 0.30)
    # sombrero lineal sobre los centros de los 3 huesos que doblan (el 4.º es la punta)
    w3 = np.zeros((len(s), 3))
    sc = np.clip(s, CENTROS[0], CENTROS[-1])
    for b in range(3):
        izq = CENTROS[b - 1] if b > 0 else CENTROS[0] - 1
        der = CENTROS[b + 1] if b < 2 else CENTROS[-1] + 1
        w3[:, b] = np.where(sc <= CENTROS[b], (sc - izq) / (CENTROS[b] - izq), (der - sc) / (der - CENTROS[b]))
    w3 = np.clip(w3, 0, 1); w3 /= w3.sum(1, keepdims=True)
    movil = ids < len(cadenas)                                   # mechones sin cadena (cobertura): fijos a Head
    ch = np.array(cadenas)[np.minimum(ids, len(cadenas) - 1)]    # (m, 4) joints de la cadena de cada vértice
    h = np.where(movil, h, 1.0)
    J[n_base:, 0] = j_cabeza; W[n_base:, 0] = h
    for b in range(3):
        J[n_base:, b + 1] = np.where(movil, ch[:, b], 0); W[n_base:, b + 1] = (1 - h) * w3[:, b]
    return J, W


def config(nombres_cadenas, centro_colision, radio_colision, cabeza="Head", **kw):
    """Bloque para extras del nodo del pelo; lo lee alth_resortes.gd."""
    r = dict(RESORTE, **kw)
    return {"resortes": {"cadenas": nombres_cadenas, "rigidez": r["rigidez"], "arrastre": r["arrastre"],
                         "gravedad": r["gravedad"], "radio": r["radio"],
                         "colision": {"hueso": cabeza, "centro": [float(x) for x in centro_colision],
                                      "radio": float(radio_colision)}}}
