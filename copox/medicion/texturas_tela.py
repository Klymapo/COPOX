"""SENKU · texturas pequeñas de tela (19 oct 2026). Admin: "Debe de tener la textura que le corresponde" → texturas
pequeñas y repetibles por tela, generadas aquí con NumPy (licencia propia, presupuesto cero).

Cada textura es una MODULACIÓN en gris (media ≈ MEDIA, rango ±8 %) del color base de la paleta: el material lleva
baseColorFactor = color / MEDIA, así el color promedio que se ve sigue siendo el de la paleta (CHXP V3 revisa el
promedio, no los píxeles). Brief: docs/investigacion/ropa_capas.md (tafetán, sarga, satén; Permanent Style, NPS).

Telas: tafetan (algodón de camisa), sarga (lana del pantalón, diagonal), lana_cerrada (chaleco), saten (seda de
corbata, brillo en bandas), cuero (zapato), lona (tenis).
También: UV por proyección de caja (cada cara usa el plano de su normal dominante) con `escala` repeticiones por
unidad del modelo.
"""
from __future__ import annotations

import io

import numpy as np

MEDIA = 0.92
TAM = 128
ESCALAS = {"tafetan_suave": 35.0, "tafetan": 90.0, "sarga": 70.0, "lana_cerrada": 110.0, "saten": 45.0, "cuero": 60.0, "lona": 80.0}
RUGOSIDAD = {"tafetan_suave": 0.9, "tafetan": 0.9, "sarga": 0.9, "lana_cerrada": 0.95, "saten": 0.55, "cuero": 0.6, "lona": 0.92}


def _norm(a, amp=0.08, media=MEDIA):
    amp = min(amp, 1 - media)                     # sin recortar arriba: el promedio queda exacto
    a = a - a.mean()
    a = a / max(np.abs(a).max(), 1e-9)
    return np.clip(media + amp * a, 0, 1)


def patron(tela, n=TAM, semilla=0, media=MEDIA):
    def nrm(a, amp=0.08):                        # misma media para todas las telas
        return _norm(a, amp, media)
    rng = np.random.default_rng(semilla)
    y, x = np.mgrid[0:n, 0:n]
    ruido = rng.normal(0, 1, (n, n))
    from scipy.ndimage import gaussian_filter
    if tela == "tafetan_suave":                  # camisa (Admin: "se ven píxeles"): trama grande, borrosa y muy tenue
        k = 8
        a = gaussian_filter(((x // k + y // k) % 2) * 1.0, 2.0, mode="wrap") + 0.4 * gaussian_filter(ruido, 3, mode="wrap")
        return nrm(a, 0.022)
    if tela == "tafetan":                        # trama 1×1: urdimbre y trama se alternan
        k = 4
        a = ((x // k + y // k) % 2) * 1.0 + 0.35 * gaussian_filter(ruido, 0.8, mode="wrap")
    elif tela == "sarga":                        # diagonal 2/2
        k = 6
        a = (((x + y) // k) % 2) * 1.0 + 0.25 * np.sin(2 * np.pi * x / k) + 0.3 * gaussian_filter(ruido, 0.7, mode="wrap")
    elif tela == "lana_cerrada":                 # tejido cerrado: puntitos con poca dirección
        a = gaussian_filter(ruido, 1.2, mode="wrap") + 0.3 * (((x // 3) + (y // 3)) % 2)
    elif tela == "saten":                        # brillo largo en bandas diagonales suaves
        a = np.sin(2 * np.pi * (x + 2 * y) / n * 3) + 0.15 * gaussian_filter(ruido, 2, mode="wrap")
        return nrm(a, 0.05)
    elif tela == "cuero":                        # grano irregular
        a = gaussian_filter(ruido, 1.6, mode="wrap") - 0.6 * gaussian_filter(ruido, 4.0, mode="wrap")
    elif tela == "lona":
        k = 3
        a = ((x // k) % 2) * 0.6 + ((y // k) % 2) * 0.6 + 0.3 * gaussian_filter(ruido, 0.6, mode="wrap")
    else:
        raise ValueError(tela)
    return nrm(a)


def png(tela, semilla=0, media=MEDIA):
    from PIL import Image
    g = (patron(tela, semilla=semilla, media=media) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(np.stack([g, g, g], -1)).save(buf, "PNG", optimize=True)
    return buf.getvalue()


def uv_caja(V, T, escala):
    """UV por cara (vértices ya duplicados por esquina, como tras el facetado o expandidos): plano de la normal
    dominante de cada cara. Devuelve UV por vértice (len(V), 2)."""
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    eje = np.abs(fn).argmax(1)
    UV = np.zeros((len(V), 2), np.float32)
    for e, (a, b) in ((0, (2, 1)), (1, (0, 2)), (2, (0, 1))):
        sel = T[eje == e].ravel()
        UV[sel] = V[sel][:, [a, b]] * escala
    return UV


def material_textura(E, nombre, hexa, tela):
    """Material con textura de tela embebida en el GLB. baseColorFactor = color de la paleta / MEDIA."""
    j = E.j
    for i, m in enumerate(j.get("materials", [])):
        if m["name"] == nombre:
            return i
    col = np.array([int(hexa[k:k + 2], 16) / 255 for k in (1, 3, 5)])
    media = max(MEDIA, float(col.max()) + 0.004)  # colores claros: textura más sutil para no pasar de 1
    datos = png(tela, media=min(media, 0.996))
    while len(E.out) % 4:
        E.out.append(0)
    j["bufferViews"].append({"buffer": 0, "byteOffset": len(E.out), "byteLength": len(datos)})
    E.out.extend(datos)
    j.setdefault("images", []).append({"bufferView": len(j["bufferViews"]) - 1, "mimeType": "image/png",
                                       "name": f"TELA_{tela.upper()}"})
    j.setdefault("samplers", []).append({"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497})
    j.setdefault("textures", []).append({"sampler": len(j["samplers"]) - 1, "source": len(j["images"]) - 1})
    lin = np.where(col <= 0.04045, col / 12.92, ((col + 0.055) / 1.055) ** 2.4)
    # el PNG es sRGB: su media en lineal es MEDIA_lin; el factor compensa para que el promedio sea el color
    media_lin = ((min(media, 0.996) + 0.055) / 1.055) ** 2.4
    factor = np.clip(lin / media_lin, 0, 1)
    j["materials"].append({"name": nombre, "doubleSided": True,
                           "pbrMetallicRoughness": {"baseColorFactor": [*map(float, factor), 1.0],
                                                    "baseColorTexture": {"index": len(j["textures"]) - 1},
                                                    "metallicFactor": 0, "roughnessFactor": RUGOSIDAD[tela]},
                           "extras": {"paleta": hexa, "tela": tela}})
    E.b = bytes(E.out)
    return len(j["materials"]) - 1
