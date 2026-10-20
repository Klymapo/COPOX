"""SENKU · silueta contra referencia (genérico; 19 oct 2026).

Mide un GLB contra una hoja de referencia (una o varias vistas) sin abrir Blender. Generaliza lo que se aprendió con el
pelo de Theo (pelo_arco):
- Cada hoja se describe con un JSON al lado de la imagen (`<imagen>.senku.json`): disposición (1, 2x2, columnas),
  qué vista hay en cada celda, tipo de anclas y, si hace falta, muestras de color por clase.
- Alineación por el PISO (suela / base del objeto, fila más baja del objeto) + una SEGUNDA COTA según el tipo:
    personaje_T   → línea de hombros (brazos en T) contra la altura de los hombros del esqueleto;
    personaje_pie → altura total del personaje en la hoja contra la del modelo (se avisa: la escala se SUPONE);
    objeto        → altura total contra una cota real convertida a ALTH (`cota_u` en el JSON o argumento).
  La vista principal (frente) manda; las demás se hacen consistentes con ella: misma altura de la parte más alta y,
  en la espalda, el mismo ancho. El centro horizontal sale del cuerpo/objeto, nunca de la región que se está midiendo.
- Pocas referencias: las vistas que no están en la hoja salen N-A con motivo (no se inventan). La de 3/4 sale N-A
  hasta que se calibre su ángulo.
- Comparación ortográfica en pose de reposo: IoU por vista y por franja, imagen roja/azul (rojo = sobra en el modelo,
  azul = falta), y JSON listo para CHXP.
Todo gratis: NumPy, SciPy, Pillow.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

VISTAS_ORTO = ("frente", "perfil", "espalda")


# ── hoja ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def config_hoja(ruta_img):
    p = os.path.splitext(ruta_img)[0] + ".senku.json"
    if os.path.exists(p):
        c = json.load(open(p))
    else:
        c = {"disposicion": "1", "celdas": {"frente": [0, 0]}, "anclas": "personaje_pie"}
    c.setdefault("borde", 6)
    return c


def _celdas(A, c):
    d = c["disposicion"]
    filas, cols = {"1": (1, 1), "2x2": (2, 2), "1x2": (1, 2), "1x3": (1, 3), "1x4": (1, 4)}[d]
    h, w = A.shape[0] // filas, A.shape[1] // cols
    b = int(c["borde"])
    for v, (i, j) in c["celdas"].items():
        yield v, A[i * h + b:(i + 1) * h - b, j * w + b:(j + 1) * w - b]


def _fondo(a):
    borde = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    f = np.median(borde, 0)
    d = np.abs(a - f).max(2)
    return d < 22, f


def _clases(a, c):
    """pelo / piel: muestras de color del JSON (lo más cercano dentro de tolerancia) o reglas por defecto (rubio)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = c.get("muestras")
    if m:
        out = {}
        for k, hexs in m.items():
            acc = np.zeros(a.shape[:2], bool)
            for hx in hexs:
                q = np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)])
                acc |= np.abs(a - q).max(2) < int(c.get("tolerancia", 34))
            out[k] = acc
        return out.get("pelo", np.zeros(a.shape[:2], bool)), out.get("piel", np.zeros(a.shape[:2], bool))
    pelo = (r - b > 40) & (g - b > 22) & (r - g < 38) & (r > 120)
    piel = (r - b > 45) & (r - g >= 38) & (r > 190)
    return pelo, piel


def cargar_hoja(ruta_img):
    """-> {vista: dict(img, objeto, cabeza, piso, techo, hombro, cx, oscuro)} + ['_config']"""
    from scipy.ndimage import binary_fill_holes, label, binary_opening, binary_closing
    c = config_hoja(ruta_img)
    A = np.asarray(Image.open(ruta_img).convert("RGB")).astype(int)
    out = {"_config": c}
    for v, a in _celdas(A, c):
        fondo, _ = _fondo(a)
        obj = binary_opening(~fondo, iterations=2)
        lab, n = label(obj)
        if n:                                                # el objeto principal (sin ruido ni sombras sueltas)
            tam = np.bincount(lab.ravel()); tam[0] = 0
            obj = lab == tam.argmax()
        # sombra en el piso: gris claro poco saturado bajo el objeto; fuera
        sat = a.max(2) - a.min(2)
        sombra = (sat < 14) & (a.mean(2) > 120)
        obj &= ~sombra
        filas = np.nonzero(obj.any(1))[0]
        piso, techo = int(filas.max()), int(filas.min())
        oscuro = obj & ((a.sum(2)) < 300)
        pelo, piel = _clases(a, c)
        cab = binary_opening((pelo | piel) & obj, iterations=1)
        lab2, _ = label(cab)
        ids = [k for k in np.unique(lab2[techo:techo + 40]) if k]
        cab = binary_fill_holes(binary_closing(np.isin(lab2, ids), iterations=6))
        ancho = obj.sum(1)
        hombro = cx = None
        if c.get("anclas") == "personaje_T" and v in ("frente", "espalda"):
            fil = np.nonzero(ancho > 0.7 * ancho.max())[0]
            hombro = float(fil.mean())
            cols = np.nonzero(obj[fil].any(0))[0]
            cx = float(cols.min() + cols.max()) / 2
        else:
            cols = np.nonzero(obj.any(0))[0]
            cx = float(cols.min() + cols.max()) / 2
        out[v] = dict(img=a.astype(np.uint8), objeto=obj, cabeza=cab, piso=piso, techo=techo, hombro=hombro, cx=cx,
                      oscuro=oscuro)
    return out


# ── modelo ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def esqueleto(E_o_glb):
    from .gltf import accesor, leer_glb
    j, b = leer_glb(E_o_glb) if isinstance(E_o_glb, str) else (E_o_glb.j, E_o_glb.b)
    if not j.get("skins"):
        return {}
    sk = j["skins"][0]
    ibm = accesor(j, b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return {j["nodes"][k]["name"]: np.linalg.inv(ibm[i])[:3, 3] for i, k in enumerate(sk["joints"])}


def malla_visible(glb, ocultar=(), y_min=None, y_max=None):
    """Triángulos de los nodos visibles (KHR_node_visibility) en pose de reposo; opcionalmente una franja en y."""
    from .gltf import Modelo
    M = Modelo(glb)
    Vs, Ts, n = [], [], 0
    for p in M.prims:
        nd = M.j["nodes"][p.nodo]
        if not nd.get("extensions", {}).get("KHR_node_visibility", {}).get("visible", True):
            continue
        if nd.get("name", "") in ocultar:
            continue
        T = p.indices
        y = p.pos[T][:, :, 1]
        keep = np.ones(len(T), bool)
        if y_min is not None:
            keep &= (y > y_min).all(1)
        if y_max is not None:
            keep &= (y < y_max).all(1)
        if keep.any():
            Vs.append(p.pos); Ts.append(T[keep] + n); n += len(p.pos)
    return np.vstack(Vs), np.vstack(Ts)


ANGULOS = {"frente": (0.0, 0.0), "perfil": (90.0, 0.0), "espalda": (180.0, 0.0)}   # (giro, elevación) en grados


def _uvd(P, giro, elev):
    """Ortográfica con cámara girada `giro` alrededor de y (0 = frente, 90 = lado derecho del personaje) y elevada
    `elev` (mira hacia abajo). -> u (derecha), v (arriba), profundidad (hacia la cámara)."""
    a, e = np.radians(giro), np.radians(elev)
    u = P[:, 0] * np.cos(a) + P[:, 2] * np.sin(a)
    prof = -P[:, 0] * np.sin(a) + P[:, 2] * np.cos(a)
    v = P[:, 1] * np.cos(e) - prof * np.sin(e)
    prof2 = prof * np.cos(e) + P[:, 1] * np.sin(e)
    return u, v, prof2


def _uv(P, vista):
    u, v, _ = _uvd(P, *ANGULOS[vista])
    return u, v


# ── alineación ──────────────────────────────────────────────────────────────────────────────────────────────────────
def alinear(hoja, joints=None, altura_modelo=None, cota_u=None, consistente=True):
    """-> ({vista: (escala px/u, u0 px, piso px)}, avisos). px = u0 + u·escala ; fila = piso − y·escala."""
    c = hoja["_config"]
    tipo = c.get("anclas", "personaje_pie")
    avisos = []
    vistas = [v for v in VISTAS_ORTO if v in hoja]
    if "frente" not in hoja:
        avisos.append("sin vista de frente: la primera vista disponible manda")
    v0 = "frente" if "frente" in hoja else vistas[0]
    r0 = hoja[v0]
    al = {}
    if tipo == "personaje_T" and joints:
        y_h = float((joints["LeftUpperArm"][1] + joints["RightUpperArm"][1]) / 2)
        esc = (r0["piso"] - r0["hombro"]) / y_h
    else:
        alto = cota_u or c.get("cota_u") or altura_modelo
        if not alto:
            raise ValueError("falta la segunda cota (altura del modelo o cota_u)")
        if tipo == "personaje_pie":
            avisos.append("escala SUPUESTA: la altura total de la hoja = la del modelo (no mide la estatura)")
        esc = (r0["piso"] - r0["techo"]) / float(alto)
    al[v0] = (esc, r0["cx"], r0["piso"])
    if consistente:
        # consistencia ENTRE vistas de la hoja (solo datos de la hoja, el modelo no interviene): misma parte más alta y
        # mismo ancho. Con cabeza segmentada en ambas vistas se usa la cabeza (la perspectiva deforma menos que los
        # brazos abiertos); si no, el objeto entero.
        usa_cab = all(hoja[v]["cabeza"].any() for v in vistas)
        clave = "cabeza" if usa_cab else "objeto"
        t0 = int(np.nonzero(r0[clave].any(1))[0].min())
        y_top = (r0["piso"] - t0) / esc
        c0, c1 = _cols(r0[clave], 0, r0[clave].shape[0] - 1)
        ancho = (c1 - c0) / esc
        for v in vistas:
            if v == v0:
                continue
            r = hoja[v]
            if v == "espalda" and v0 == "frente":
                b0, b1 = _cols(r[clave], 0, r[clave].shape[0] - 1)
                e = (b1 - b0) / ancho
            else:
                e = esc
            t = int(np.nonzero(r[clave].any(1))[0].min())
            piso = t + y_top * e                         # misma parte más alta en todas las vistas
            if v == "espalda" and v0 == "frente" and usa_cab:     # centro: el de la cabeza, igual que en el frente
                x_c = ((c0 + c1) / 2 - r0["cx"]) / esc
                r = dict(r, cx=(b0 + b1) / 2 + x_c * e)
            u0 = r["cx"]
            if v == "perfil" and joints and "Chest" in joints:   # torso (ropa oscura) entre hombro y cadera
                f0 = int(piso - joints["LeftUpperArm"][1] * e); f1 = int(piso - joints["Hips"][1] * e)
                cols = np.nonzero(r["oscuro"][max(f0, 0):max(f1, 1)].any(0))[0]
                if len(cols):
                    u0 = float(cols.min() + cols.max()) / 2 - float(joints["Chest"][2]) * e
            al[v] = (e, u0, piso)
    for v in ("perfil", "espalda", "tres_cuartos"):
        if v not in hoja:
            avisos.append(f"{v}: N-A (no está en la hoja)")
    if "tres_cuartos" in hoja:
        avisos.append("tres_cuartos: N-A (ángulo sin calibrar)")
    return al, avisos


def _cols(m, f0, f1):
    cols = np.nonzero(m[f0:f1 + 1].any(0))[0]
    return float(cols.min()), float(cols.max())


def calibrar_tres_cuartos(glb, hoja, al, giros=range(-60, -19, 5), elevs=(12, 20, 28, 36, 44), escalas=(0.9, 1.0, 1.1),
                          ocultar=()):
    """La celda de 3/4 no trae ángulo: se busca (giro, elevación) y posición que mejor calcan el CUERPO del modelo
    (sin cabeza ni pelo: lo que se va a medir no se usa para alinear) contra el cuerpo de la hoja. Escala = frente.
    Guarda el ángulo en ANGULOS y la alineación en `al`. -> dict con el resultado."""
    from scipy.ndimage import binary_dilation
    if "tres_cuartos" not in hoja or "frente" not in al:
        return None
    r = hoja["tres_cuartos"]
    ref = r["objeto"] & ~binary_dilation(r["cabeza"], iterations=6)
    J = esqueleto(glb)
    y_cuello = float(J["Neck"][1]) if "Neck" in J else 0.47
    V, T = malla_visible(glb, ocultar, y_max=y_cuello)
    e0 = al["frente"][0]
    H, W = ref.shape
    F_ref = np.fft.rfft2(ref.astype(np.float32))
    mejor = None
    for g in giros:
      for el in elevs:
        for fe in escalas:
            e = e0 * fe
            ANGULOS["tres_cuartos"] = (float(g), float(el))
            u, v, _ = _uvd(V, g, el)
            u0 = W / 2 - (u.min() + u.max()) / 2 * e
            piso = H / 2 + (v.min() + v.max()) / 2 * e
            m = mascara_modelo(V, T, "tres_cuartos", {"tres_cuartos": (e, u0, piso)}, ref.shape)
            # mejor desplazamiento por correlación (FFT): máximo solapamiento
            corr = np.fft.irfft2(F_ref * np.conj(np.fft.rfft2(m.astype(np.float32))), s=ref.shape)
            dy, dx = np.unravel_index(np.argmax(corr), corr.shape)
            dy = dy - H if dy > H // 2 else dy
            dx = dx - W if dx > W // 2 else dx
            inter = corr.max()
            iou = inter / (ref.sum() + m.sum() - inter)
            if mejor is None or iou > mejor[0]:
                mejor = (float(iou), float(g), float(el), u0 + dx, piso + dy, e)
    iou, g, el, u0, piso, e = mejor
    ANGULOS["tres_cuartos"] = (g, el)
    al["tres_cuartos"] = (e, u0, piso)
    return {"giro": g, "elevacion": el, "escala_rel": round(e / e0, 3), "iou_cuerpo": round(iou, 4),
            "aviso": "la celda de 3/4 tiene perspectiva fuerte; la ortográfica solo la aproxima"}


# ── comparación ─────────────────────────────────────────────────────────────────────────────────────────────────────
def mascara_modelo(V, T, vista, al, forma):
    from ..render.raster import rasterizar
    e, u0, piso = al[vista][:3]
    u, y, prof = _uvd(V, *ANGULOS[vista])
    X = (u0 + u * e)[T]; Y = (piso - y * e)[T]
    prof = prof[T]
    tri, _, _ = rasterizar(X, Y, prof, forma)
    return tri >= 0


def comparar(V, T, hoja, al, clave="objeto", franjas=None, salida=None):
    """IoU por vista (clave = 'objeto' o 'cabeza'); franjas = {nombre: (y_min_u, y_max_u)} en unidades del modelo."""
    res, imgs = {}, []
    for v in VISTAS_ORTO + (("tres_cuartos",) if "tres_cuartos" in al else ()):
        if v not in al:
            res[v] = "N-A"
            continue
        m_ref = hoja[v][clave]
        m_mod = mascara_modelo(V, T, v, al, m_ref.shape)
        fila = {"iou": _iou(m_ref, m_mod)}
        e, u0, piso = al[v][:3]
        for nombre, (y0, y1) in (franjas or {}).items():
            a = int(max(piso - y1 * e, 0)); b = int(min(piso - y0 * e, m_ref.shape[0]))
            fila[nombre] = _iou(m_ref[a:b], m_mod[a:b])
        res[v] = fila
        imgs.append(_overlay(m_ref, m_mod))
    vals = [res[v]["iou"] for v in res if isinstance(res[v], dict)]
    res["media"] = round(float(np.mean(vals)), 4) if vals else "N-A"
    if salida and imgs:
        hmax = max(i.size[1] for i in imgs)
        hoja_img = Image.new("RGB", (sum(i.size[0] for i in imgs) + 20 * len(imgs), hmax), (236, 236, 236))
        x = 0
        for i in imgs:
            hoja_img.paste(i, (x, 0)); x += i.size[0] + 20
        hoja_img.save(salida)
    return res


def _iou(a, b):
    return round(float((a & b).sum() / max((a | b).sum(), 1)), 4)


def _overlay(m_ref, m_mod):
    o = np.full(m_ref.shape + (3,), 236, np.uint8)
    o[m_ref & m_mod] = 255; o[m_mod & ~m_ref] = (215, 60, 50); o[m_ref & ~m_mod] = (50, 90, 215)
    ys, xs = np.nonzero(m_ref | m_mod)
    if len(ys):
        o = o[max(ys.min() - 20, 0):ys.max() + 20, max(xs.min() - 20, 0):xs.max() + 20]
    return Image.fromarray(o)


def auditar(glb, ruta_hoja, region="objeto", ocultar=(), salida=None, cota_u=None):
    """Una llamada: carga hoja y modelo, alinea, compara. region='cabeza' → solo cabeza (y > cuello) vs pelo∪piel."""
    hoja = cargar_hoja(ruta_hoja)
    J = esqueleto(glb)
    V0, T0 = malla_visible(glb, ocultar)
    altura = float(V0[:, 1].max() - min(V0[:, 1].min(), 0.0))
    al, avisos = alinear(hoja, J, altura_modelo=altura, cota_u=cota_u)
    if region == "cabeza":
        y_c = float(J["Neck"][1]) if "Neck" in J else 0.47
        V, T = malla_visible(glb, ocultar, y_min=y_c)
        r = comparar(V, T, hoja, al, "cabeza", franjas={"pelo": (y_c + 0.15, 9.0)}, salida=salida)
    else:
        r = comparar(V0, T0, hoja, al, "objeto", salida=salida)
    return {"region": region, "hoja": ruta_hoja, "anclas": hoja["_config"].get("anclas"), "iou": r, "avisos": avisos,
            "escalas_px_u": {v: round(a[0], 1) for v, a in al.items()}}
