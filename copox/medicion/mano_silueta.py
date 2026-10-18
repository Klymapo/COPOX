"""SENKU · silueta de la mano abierta contra la mano con regla (refs/infografias/mano-con-regla.jpg).

Vista de palma (como la foto: palma de frente, dedos arriba, pulgar a la izquierda = mano izquierda del modelo).
Referencia: máscara de piel (color) arriba de la línea de la muñeca (y = 760). Modelo: triángulos de la pieza
'ManoL' proyectados sobre el plano de la palma (x hacia arriba, z hacia la izquierda), sin lo que queda detrás de la
muñeca. Se alinean dos puntos: centro de la muñeca y punta del dedo medio (escala, giro y traslación). Devuelve IoU,
IoU por franja (palma / dedos / pulgar) y una imagen: blanco = ambos, rojo = solo modelo, azul = solo referencia.
"""
from __future__ import annotations
import numpy as np
from PIL import Image

REF = "refs/infografias/mano-con-regla.jpg"
MUNECA_Y, MUNECA_X = 760, 410
PUNTA_MEDIO = (392, 124)


def mascara_ref(ruta=REF):
    a = np.asarray(Image.open(ruta).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    piel = (r > 190) & (r - b > 45) & (g > 120) & (g < 215) & (b < 185) & (r > g)
    piel[MUNECA_Y:, :] = False
    piel[:, 630:] = False                      # la regla
    return piel


def mascara_modelo(glb, forma, lado="L"):
    from .gltf import Modelo, accesor
    from ..render.raster import rasterizar
    M = Modelo(glb)
    j = M.j
    pr = None
    for p, gp in zip(M.prims, [q for m in j["meshes"] for q in m["primitives"]]):
        if gp.get("extras", {}).get("pieza") == "Mano" + lado:
            pr = p
    sk = j["skins"][0]
    ibm = accesor(j, M.b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    H = {j["nodes"][k]["name"]: np.linalg.inv(ibm[i])[:3, 3] for i, k in enumerate(sk["joints"])}
    P, F = pr.pos, pr.indices.reshape(-1, 3)
    W = H["LeftHand"]
    punta = P[np.argmax(P[:, 0] * (np.abs(P[:, 2] - H["LeftMiddleProximal"][2]) < 0.006))]
    # plano de palma: u = −z (izquierda en la foto = +z del modelo → pulgar a la izquierda), v = x (arriba)
    def a2d(Q):
        return np.stack([-(Q[:, 2]), Q[:, 0]], 1)
    p2, w2, t2 = a2d(P), a2d(W[None])[0], a2d(punta[None])[0]
    # similitud que lleva muñeca→(MUNECA_X, MUNECA_Y) y punta→PUNTA_MEDIO (y de imagen hacia abajo)
    A0, A1 = np.array([MUNECA_X, MUNECA_Y], float), np.array(PUNTA_MEDIO, float)
    v_m, v_i = t2 - w2, A1 - A0
    v_m_img = np.array([v_m[0], -v_m[1]])
    esc = np.linalg.norm(v_i) / np.linalg.norm(v_m_img)
    ang = np.arctan2(v_i[1], v_i[0]) - np.arctan2(v_m_img[1], v_m_img[0])
    R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    q = (p2 - w2) * [1, -1]
    img = A0 + (q @ R.T) * esc
    X, Y = img[F, 0], img[F, 1]
    Z = P[F, 1]
    tri, _, _ = rasterizar(X, Y, Z, forma)
    m = tri >= 0
    m[MUNECA_Y:, :] = False
    return m


def comparar(glb, salida=None, raiz="."):
    import os
    ref = mascara_ref(os.path.join(raiz, REF))
    mod = mascara_modelo(glb, ref.shape)
    inter, union = (ref & mod).sum(), (ref | mod).sum()
    filas = {"total": float(inter / max(union, 1))}
    for nombre, (y0, y1, x0, x1) in {"dedos": (0, 440, 200, 640), "palma": (440, 760, 230, 640),
                                      "pulgar": (380, 760, 0, 260)}.items():
        r, m = ref[y0:y1, x0:x1], mod[y0:y1, x0:x1]
        filas[nombre] = float((r & m).sum() / max((r | m).sum(), 1))
    if salida:
        o = np.full(ref.shape + (3,), 236, np.uint8)
        o[ref & mod] = (255, 255, 255); o[mod & ~ref] = (220, 60, 60); o[ref & ~mod] = (60, 90, 220)
        Image.fromarray(o).save(salida)
    return filas
