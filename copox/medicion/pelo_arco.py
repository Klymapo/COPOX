"""SENKU · arco del pelo desde la hoja de referencia (Admin, 19 oct 2026: "Falta una forma de hacer el arco. Usa SENKU").

El arco (el contorno de la cabeza con pelo: cuánto sube, cuánto se abre a los lados y cómo cae atrás) se mide en la hoja
de 4 vistas (refs/personajes/joven-rubio-4-vistas.jpg) y se lleva a 3D con un CASCO VISUAL:
  1. Por vista (frente, perfil, espalda): máscara de la cabeza = pelo ∪ piel (sin ropa ni fondo), huecos rellenos.
  2. Alineación con el esqueleto del modelo (sin mirar la cabeza, para no hacer trampa): piso (suela más baja) y línea
     de hombros (los brazos en T) dan escala y altura; el centro del cuerpo da la posición horizontal. En perfil la
     escala es la de frente (misma hoja) y el centro horizontal sale del torso.
  3. Casco: desde el centro del cráneo, por cada dirección, el radio máximo cuyo punto proyecta DENTRO de la cabeza en
     todas las vistas. Con tres vistas ortogonales el corte horizontal sale rectangular: se redondea con una
     superelipse que pasa por los mismos extremos.
  4. `arco(H, ...)` devuelve el radio objetivo de la superficie exterior del pelo por dirección. La receta pone la
     base del cráneo debajo y los mechones encima siguiendo ese arco.
`comparar(...)` mide IoU de la silueta de la cabeza modelo contra la hoja por vista y por franja (arriba = pelo).
"""
from __future__ import annotations

import numpy as np
from PIL import Image

REF = "refs/personajes/joven-rubio-4-vistas.jpg"
CUADRANTES = {"frente": (0, 0), "perfil": (0, 1), "espalda": (1, 0), "tres_cuartos": (1, 1)}


def _segmentar(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    pelo = (r - b > 40) & (g - b > 22) & (r - g < 38) & (r > 120)
    piel = (r - b > 45) & (r - g >= 38) & (r > 190)
    fondo = (np.abs(r - g) < 14) & (np.abs(g - b) < 16) & (r > 185)
    oscuro = (r + g + b) < 300
    return pelo, piel, fondo, oscuro


def vistas_ref(ruta=REF):
    """-> {vista: dict(cabeza=mask, piso=fila, hombro=fila|None, cx=col del cuerpo, torso_cx=col, img=rgb)}"""
    from scipy.ndimage import binary_fill_holes, label, binary_opening, binary_closing
    A = np.asarray(Image.open(ruta).convert("RGB")).astype(int)
    h, w = A.shape[0] // 2, A.shape[1] // 2
    out = {}
    for v, (i, j) in CUADRANTES.items():
        a = A[i * h:(i + 1) * h, j * w:(j + 1) * w]
        a = a[6:-6, 6:-6]                                    # sin la línea divisoria
        pelo, piel, fondo, oscuro = _segmentar(a)
        cuerpo = ~fondo
        cuerpo = binary_opening(cuerpo, iterations=2)
        filas = np.nonzero(oscuro.any(1))[0]
        piso = int(filas.max())
        # la cabeza: componente de pelo ∪ piel que toca la fila más alta del cuerpo
        cab = binary_opening(pelo | piel, iterations=1)
        lab, n = label(cab)
        top = np.nonzero(cuerpo.any(1))[0].min()
        ids = [k for k in np.unique(lab[top:top + 40]) if k]
        cab = np.isin(lab, ids)
        cab = binary_fill_holes(binary_closing(cab, iterations=6))   # ojos, cejas y oreja quedan dentro
        # hombros: banda de los brazos en T (filas con el cuerpo más ancho)
        ancho = cuerpo.sum(1)
        hombro = None
        if v in ("frente", "espalda"):
            fil = np.nonzero(ancho > 0.7 * ancho.max())[0]
            hombro = float(fil.mean())
            cols = np.nonzero(cuerpo[fil].any(0))[0]
            cx = float(cols.min() + cols.max()) / 2
        else:
            cx = None
        # torso: ropa oscura entre hombros y cadera (perfil): centro horizontal
        out[v] = dict(cabeza=cab, piso=piso, hombro=hombro, cx=cx, oscuro=oscuro, img=a.astype(np.uint8))
    return out


def esqueleto(E_o_glb):
    """Posiciones de reposo (espacio de malla) de las articulaciones por nombre."""
    from .gltf import accesor, leer_glb
    if isinstance(E_o_glb, str):
        j, b = leer_glb(E_o_glb)
    else:
        j, b = E_o_glb.j, E_o_glb.b
    sk = j["skins"][0]
    ibm = accesor(j, b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return {j["nodes"][k]["name"]: np.linalg.inv(ibm[i])[:3, 3] for i, k in enumerate(sk["joints"])}


def _uv(P, vista):
    """Proyección ortográfica: (u hacia la derecha de la imagen, y hacia arriba)."""
    if vista == "frente":
        return P[:, 0], P[:, 1]
    if vista == "espalda":
        return -P[:, 0], P[:, 1]
    if vista == "perfil":                                    # cámara del lado derecho del personaje: nariz a la derecha
        return P[:, 2], P[:, 1]
    raise ValueError(vista)


def alinear(ref, joints, torso_z=None):
    """-> {vista: (escala px/u, u0 px, piso px)}: px = u0 + u·escala ; fila = piso − y·escala."""
    y_hombro = float((joints["LeftUpperArm"][1] + joints["RightUpperArm"][1]) / 2)
    al = {}
    f = ref["frente"]
    esc = (f["piso"] - f["hombro"]) / y_hombro
    for v in ("frente", "espalda"):
        r = ref[v]
        e = (r["piso"] - r["hombro"]) / y_hombro
        al[v] = (e, r["cx"], r["piso"])
    # perfil: escala de frente; horizontal por el torso oscuro (filas entre hombro y cadera)
    r = ref["perfil"]
    y_cadera = float(joints["Hips"][1])
    f0, f1 = int(r["piso"] - y_hombro * esc), int(r["piso"] - y_cadera * esc)
    cols = np.nonzero(r["oscuro"][f0:f1].any(0))[0]
    zc = float(torso_z if torso_z is not None else joints["Chest"][2])
    al["perfil"] = (esc, float(cols.min() + cols.max()) / 2 - zc * esc, r["piso"])
    return al


def casco(c, D, ref, al, r0, r1, paso=0.0015, vistas=("frente", "perfil", "espalda"), n_super=2.6):
    """Radio máximo (desde c, por dirección D) que queda dentro de la cabeza en todas las vistas. Busca de r0 a r1."""
    rs = np.arange(r0, r1, paso)
    dentro = np.ones((len(D), len(rs)), bool)
    for v in vistas:
        e, u0, piso = al[v]
        m = ref[v]["cabeza"]
        for k, r in enumerate(rs):
            P = c + D * r
            u, y = _uv(P, v)
            col = np.round(u0 + u * e).astype(int); fil = np.round(piso - y * e).astype(int)
            ok = (col >= 0) & (col < m.shape[1]) & (fil >= 0) & (fil < m.shape[0])
            ins = np.zeros(len(D), bool)
            ins[ok] = m[fil[ok], col[ok]]
            dentro[:, k] &= ins
    # radio = último r dentro, contando desde adentro sin huecos
    fuera = ~dentro
    primero_fuera = np.where(fuera.any(1), fuera.argmax(1), len(rs))
    R = r0 + paso * np.maximum(primero_fuera - 1, 0)
    # redondear el corte horizontal (tres vistas ortogonales dejan esquinas de caja): superelipse por los extremos
    dx, dz = D[:, 0], D[:, 2]
    hor = np.sqrt(dx * dx + dz * dz) + 1e-9
    # extremos por elevación (franjas de 5°)
    el = np.degrees(np.arcsin(np.clip(D[:, 1], -1, 1)))
    Rr = R.copy()
    for e0 in range(-90, 90, 5):
        s = (el >= e0) & (el < e0 + 5)
        if s.sum() < 8:
            continue
        X = (R[s] * dx[s]); Z = (R[s] * dz[s])
        ax, bz = np.abs(X).max(), np.abs(Z).max()
        # radio de la superelipse en la dirección horizontal de cada punto (en el plano de la franja)
        cx, cz = np.abs(dx[s] / hor[s]), np.abs(dz[s] / hor[s])
        rh = 1.0 / ((cx / max(ax, 1e-6)) ** n_super + (cz / max(bz, 1e-6)) ** n_super) ** (1 / n_super)
        Rr[s] = np.minimum(R[s], rh / np.maximum(hor[s], 1e-3))   # a radio r la extensión horizontal es r·hor
    return Rr, R


def mascara_modelo(V, T, vista, al, forma):
    from ..render.raster import rasterizar
    e, u0, piso = al[vista]
    u, y = _uv(V, vista)
    X = (u0 + u * e)[T]; Y = (piso - y * e)[T]
    prof = {"frente": V[:, 2], "espalda": -V[:, 2], "perfil": -V[:, 0]}[vista][T]
    tri, _, _ = rasterizar(X, Y, prof, forma)
    return tri >= 0


def comparar(V, T, ref, al, y_corte_px=None, salida=None):
    """IoU de la cabeza (malla ya filtrada a cabeza + pelo) contra la hoja; franja alta = arriba de y_corte (pelo)."""
    filas = {}
    imgs = []
    for v in ("frente", "perfil", "espalda"):
        m_ref = ref[v]["cabeza"]
        m_mod = mascara_modelo(V, T, v, al, m_ref.shape)
        corte = int(y_corte_px[v]) if y_corte_px else m_ref.shape[0]
        a, b = m_ref[:corte], m_mod[:corte]
        filas[v] = round(float((a & b).sum() / max((a | b).sum(), 1)), 4)
        o = np.full(m_ref.shape + (3,), 236, np.uint8)
        o[m_ref & m_mod] = 255; o[m_mod & ~m_ref] = (215, 60, 50); o[m_ref & ~m_mod] = (50, 90, 215)
        if y_corte_px:
            o[corte, :] = (0, 0, 0)
        ys, xs = np.nonzero(m_ref | m_mod)
        if len(ys):
            o = o[max(ys.min() - 20, 0):min(ys.max() + 20, o.shape[0]), max(xs.min() - 20, 0):min(xs.max() + 20, o.shape[1])]
        imgs.append(Image.fromarray(o))
    filas["media"] = round(float(np.mean([filas[v] for v in ("frente", "perfil", "espalda")])), 4)
    if salida:
        hmax = max(i.size[1] for i in imgs)
        hoja = Image.new("RGB", (sum(i.size[0] for i in imgs) + 20 * len(imgs), hmax), (236, 236, 236))
        x = 0
        for i in imgs:
            hoja.paste(i, (x, 0)); x += i.size[0] + 20
        hoja.save(salida)
    return filas


def arco(H, c, ref, al, espesor, r1=0.40, minimo=0.0, maximo=0.12, el_min=-25.0):
    """Radio de la BASE del pelo por dirección (H.D) para que la superficie exterior (base + mechones de `espesor`)
    llegue al casco de la hoja. Solo en el área de pelo y sobre `el_min`; acotado alrededor del radio original."""
    Rr, _ = casco(c, H.D, ref, al, r0=float(H.Rd.min()) * 0.6, r1=r1)
    el = np.degrees(np.arcsin(np.clip(H.D[:, 1], -1, 1)))
    obj = np.clip(Rr - espesor, H.Rd + minimo, H.Rd + maximo)
    peso = np.clip((el - el_min) / 15.0, 0, 1) * np.clip((H.Md - 0.75) / 0.25, 0, 1) ** 2   # la orilla queda pegada a la piel
    return H.Rd + (obj - H.Rd) * peso, Rr
