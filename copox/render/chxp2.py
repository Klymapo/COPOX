"""CHXP V2 · render de revisión ALTH con Godot real, por lotes (un solo proceso para muchas tomas).

Godot (copox/godot/chxp2/chxp2.gd) escribe por imagen cuatro pasadas: color (luz ALTH, sombras, MSAA), normales,
profundidad y máscara por pieza. Aquí se compone:
  - sombra de contacto (AO en espacio de pantalla, desde profundidad y normales);
  - hoja de contacto vertical (para el cel) con la referencia lado a lado y la tira de paleta;
  - GIF de clips (idle, caminar, correr);
  - reporte JSON: caja (altura en u), triángulos, piezas visibles y su cobertura en px, colores fuera de paleta.

Uso rápido (ver LEEME_IA.md):
  python -m copox.render.chxp2 ADAN_V49_VESTIDO.glb --silueta ADAN_V49.glb --ref refs/personajes/adan/... \
      --vistas personaje --gif Idle-loop,Walk-loop,Run-loop --salida /tmp/chxp2_adan
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
PROYECTO = os.path.join(RAIZ, "copox", "godot")
GODOT = os.environ.get("GODOT_BIN", "/home/claude/godot/Godot_v4.7.2-stable_linux.x86_64")

VISTAS = {
    "personaje": [("frente", 0, 8), ("tres_cuartos", 35, 10), ("perfil", 90, 6), ("espalda", 180, 8)],
    "objeto": [("frente", 0, 15), ("tres_cuartos", 40, 25), ("perfil", 90, 15), ("espalda", 180, 15)],
    "edificio": [("frente", 0, 12), ("tres_cuartos", 40, 25), ("espalda", 180, 12), ("cenital", 0, 89)],
}
LEJOS_PROF = 8.0


# ── Godot ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def correr_godot(trabajo: dict, ruta_trabajo: str, timeout=3600) -> dict:
    os.makedirs(trabajo["salida"], exist_ok=True)
    trabajo.setdefault("lejos_prof", LEJOS_PROF)
    with open(ruta_trabajo, "w") as f:
        json.dump(trabajo, f)
    cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24", GODOT, "--path", PROYECTO, "--rendering-driver", "opengl3",
           "--script", "res://chxp2/chxp2.gd", "--", ruta_trabajo]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if "CHXP2 OK" not in r.stdout:
        errores = [x for x in (r.stdout + r.stderr).splitlines() if "ERROR" in x and "UVs are required" not in x]
        raise RuntimeError("CHXP2: Godot no terminó.\n" + "\n".join(errores[-15:]))
    return {"segundos_godot": round(time.time() - t0, 1)}


# ── composición ───────────────────────────────────────────────────────────────────────────────────────────────────
def _leer(ruta):
    from PIL import Image
    return np.asarray(Image.open(ruta).convert("RGB")).astype(np.float32) / 255.0


def profundidad(img):
    """RG (16 bits) → distancia normalizada; fondo (azul sin pieza) = 1."""
    lin = img ** (1 / GAMMA_SALIDA)
    d = lin[..., 0] + lin[..., 1] / 255.0
    hay = img[..., 2] > 0.9
    return np.where(hay, d, 1.0), hay


def ao(prof, hay, radio=14, muestras=16, fuerza=1.0, rango=0.02, oclusor=None):
    """AO en pantalla: un punto se oscurece si sus vecinos en un disco quedan MÁS CERCA de la cámara de lo que daría
    el plano local (se resta la pendiente: el piso y las caras planas no se sombrean solas). Solo cuentan diferencias
    dentro de un rango, para que el fondo lejano no oscurezca."""
    gy, gx = np.gradient(prof)
    occ = np.zeros_like(prof)
    ang = np.linspace(0, 2 * np.pi, muestras, endpoint=False)
    for k, a in enumerate(ang):
        r = radio * (0.35 + 0.65 * ((k * 0.618) % 1.0))
        dx, dy = int(round(np.cos(a) * r)), int(round(np.sin(a) * r))
        vec = np.roll(np.roll(prof, -dy, 0), -dx, 1)
        esperado = prof + gx * dx + gy * dy
        dif = esperado - vec
        cuenta = (dif < rango * 4)
        if oclusor is not None:                     # solo el asset hace sombra (el piso no se sombrea a sí mismo)
            cuenta = cuenta & np.roll(np.roll(oclusor, -dy, 0), -dx, 1)
        occ += np.clip(dif / rango, 0, 1) * cuenta
    a = 1 - fuerza * occ / muestras
    from scipy.ndimage import gaussian_filter
    a = gaussian_filter(a, 1.2)
    return np.where(hay, np.clip(a, 0, 1), 1.0)


def componer_imagen(color, prof_img, fuerza_ao=0.85, ids=None):
    p, hay = profundidad(prof_img)
    a = ao(p, hay, fuerza=fuerza_ao, oclusor=(ids > 0) if ids is not None else None)
    return np.clip(color * a[..., None], 0, 1), a


GAMMA_SALIDA = 1.15      # medido: el renderer Compatibility entrega ~v**1.15 en las pasadas sin luz


def _rejilla_ids(n=124):
    k = np.arange(1, n + 1)
    c = np.stack([(k % 5) / 4.0, ((k // 5) % 5) / 4.0, ((k // 25) % 5) / 4.0], 1)
    return k, c ** GAMMA_SALIDA


def decodificar_mascara(img, fondo=None):
    """Color más cercano de la rejilla de 125; lo que esté lejos de todos (fondo, piso) = 0."""
    k, c = _rejilla_ids()
    from scipy.spatial import cKDTree
    d, j = cKDTree(c).query(img.reshape(-1, 3))
    ids = np.where(d < 0.06, k[j], 0).reshape(img.shape[:2])
    return ids


def vista_previa_mascara(ids):
    rng = np.random.default_rng(3)
    pal = rng.uniform(0.25, 0.95, (int(ids.max()) + 2, 3)); pal[0] = (0.89, 0.886, 0.913)
    return pal[ids]


# ── paleta ────────────────────────────────────────────────────────────────────────────────────────────────────────
def _lab(rgb):
    rgb = np.asarray(rgb, float)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def paleta_spec():
    with open(os.path.join(RAIZ, "spec", "alth_spec.json")) as f:
        p = json.load(f)["paleta"]
    out = {}

    def rec(d, pre=""):
        for k, v in d.items():
            if isinstance(v, dict):
                rec(v, pre + k + "/")
            elif isinstance(v, list):
                for i, c in enumerate(v):
                    if isinstance(c, str) and c.startswith("#"):
                        out[f"{pre}{k}/{i + 1}"] = c
            elif isinstance(v, str) and v.startswith("#"):
                out[pre + k] = v
    rec(p)
    return out


def _hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def revisar_paleta(piezas, tolerancia=6.0):
    """Color base de cada material (sRGB) contra la paleta de spec: ΔE76 al tono más cercano. Los materiales con
    textura (ojos, cejas) no traen color base útil y se omiten."""
    pal = paleta_spec()
    nombres = list(pal); labs = _lab(np.stack([_hex_rgb(pal[n]) for n in nombres]))
    fuera, vistos = [], set()
    for p in piezas:
        if not p.get("visible"):
            continue
        for m in p.get("materiales", []):
            c = m.get("color")
            if not c or (m.get("nombre"), c) in vistos:
                continue
            vistos.add((m.get("nombre"), c))
            lab = _lab(_hex_rgb(c))
            d = np.linalg.norm(labs - lab, axis=1); k = int(d.argmin())
            if d[k] > tolerancia:
                fuera.append({"material": m.get("nombre"), "color": "#" + c.upper(), "cercano": nombres[k],
                              "cercano_hex": pal[nombres[k]], "deltaE": round(float(d[k]), 1)})
    return fuera


# ── hoja de contacto ──────────────────────────────────────────────────────────────────────────────────────────────
def _fuente(t):
    from PIL import ImageFont
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(f):
            return ImageFont.truetype(f, t)
    return ImageFont.load_default()


CUADRANTES_2X2 = {"frente": (0, 0), "perfil": (1, 0), "espalda": (0, 1), "tres_cuartos": (1, 1)}


def ref_por_vista(ref, vista, hoja2x2):
    if ref is None or not hoja2x2 or vista not in CUADRANTES_2X2:
        return ref
    c, f = CUADRANTES_2X2[vista]
    w, h = ref.width // 2, ref.height // 2
    return ref.crop((c * w, f * h, (c + 1) * w, (f + 1) * h))


def hoja_vertical(paneles, titulo, sub, ref=None, ancho=900, paleta=None, hoja2x2=False):
    """paneles: lista de (rótulo, imagen PIL). Con ref: cada fila = referencia (o su cuadrante) | render."""
    from PIL import Image, ImageDraw
    F, Fs = _fuente(26), _fuente(18)
    col = 2 if ref is not None else 1
    w1 = ancho // col
    filas = []
    for rot, im in paneles:
        im = im.resize((w1, int(im.height * w1 / im.width)))
        fila = Image.new("RGB", (ancho, im.height + 30), "white")
        d = ImageDraw.Draw(fila)
        if ref is not None:
            r = ref_por_vista(ref, rot, hoja2x2).copy(); r.thumbnail((w1, im.height))
            fila.paste(r, ((w1 - r.width) // 2, 30 + (im.height - r.height) // 2))
            d.text((8, 4), "referencia", fill=(90, 90, 90), font=Fs)
        fila.paste(im, (ancho - w1, 30))
        d.text((ancho - w1 + 8, 4), rot, fill="black", font=Fs)
        filas.append(fila)
    alto_pal = 70 if paleta else 0
    H = 90 + sum(f.height for f in filas) + alto_pal
    hoja = Image.new("RGB", (ancho, H), "white")
    d = ImageDraw.Draw(hoja)
    d.text((10, 10), titulo, fill="black", font=F)
    d.text((10, 50), sub, fill=(70, 70, 70), font=Fs)
    y = 90
    for f in filas:
        hoja.paste(f, (0, y)); y += f.height
    if paleta:
        n = len(paleta); w = ancho / n
        for i, (nom, hx) in enumerate(paleta):
            d.rectangle([i * w, y + 6, (i + 1) * w - 2, y + 44], fill=hx)
        d.text((10, y + 48), "paleta usada: " + ", ".join(nom for nom, _ in paleta)[:110], fill=(70, 70, 70), font=_fuente(14))
    return hoja


# ── orquestación ──────────────────────────────────────────────────────────────────────────────────────────────────
def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def render(glb, salida, silueta=None, ref=None, vistas="personaje", visible=None, clip="Idle-loop", t=0.0,
           gifs=(), cuadros_gif=16, tam=1024, tam_gif=512, vista_gif="tres_cuartos", nombre=None, ref_2x2=False):
    """Una llamada = un proceso de Godot para todas las vistas y todos los GIF de este asset."""
    from PIL import Image
    nombre = nombre or os.path.splitext(os.path.basename(glb))[0].lower()
    crudo = os.path.join(salida, "_crudo"); os.makedirs(crudo, exist_ok=True)
    vs = VISTAS[vistas] if isinstance(vistas, str) else vistas
    base = {"glb": os.path.abspath(glb), "visible": visible or {}, "silueta": os.path.abspath(silueta) if silueta else ""}
    tomas = [dict(base, nombre=nombre, vistas=[{"nombre": n, "yaw": y, "elev": e} for n, y, e in vs], clip=clip,
                  tiempos=[t])]
    gv = [v for v in vs if v[0] == vista_gif] or vs[:1]
    for g in gifs:
        tomas.append(dict(base, nombre=f"{nombre}__{g}", vistas=[{"nombre": gv[0][0], "yaw": gv[0][1], "elev": gv[0][2]}],
                          clip=g, tiempos=[i / cuadros_gif for i in range(cuadros_gif)], pasadas=["color", "profundidad", "mascara"],
                          encuadre_con_silueta=False, silueta=""))
    t0 = time.time()
    trabajo = {"tam": tam, "salida": crudo, "tomas": tomas}
    log = correr_godot(trabajo, os.path.join(crudo, "trabajo.json"))
    # vistas
    info = json.load(open(os.path.join(crudo, nombre + ".json")))
    imgs = {(i["vista"], i["pasada"]): i["archivo"] for i in info["imagenes"]}
    paneles, cobertura = [], {}
    leyenda = info["leyenda_mascara"]
    for v, _, _ in vs:
        col = _leer(imgs[(v, "color")]); pr = _leer(imgs[(v, "profundidad")])
        ids = decodificar_mascara(_leer(imgs[(v, "mascara")]))
        final, _ = componer_imagen(col, pr, ids=ids)
        im = Image.fromarray((final * 255).astype(np.uint8))
        im.save(os.path.join(salida, f"{nombre}_{v}.png"))
        Image.fromarray((vista_previa_mascara(ids) * 255).astype(np.uint8)).save(os.path.join(salida, f"{nombre}_{v}_mascara.png"))
        np.save(os.path.join(crudo, f"{nombre}_{v}_ids.npy"), ids.astype(np.uint16))
        cob = np.bincount(ids.ravel(), minlength=len(leyenda) + 1)
        # bordes con antialias pueden caer en colores de rejilla sin pieza: fuera lo que no está en la leyenda o < 16 px
        cobertura[v] = {leyenda[str(k)]: int(cob[k]) for k in range(1, len(cob)) if cob[k] >= 16 and str(k) in leyenda}
        paneles.append((v, im))
    piezas = info["piezas"]
    vis = [p for p in piezas if p["visible"]]
    fuera = revisar_paleta(piezas)
    usados = sorted({(m["nombre"], "#" + m["color"]) for p in vis for m in p["materiales"] if m.get("color")})
    caja = info["caja"]
    reporte = {
        "asset": nombre, "glb": base["glb"], "sha256": sha(glb), "alto_u": round(caja["tam"][1], 4),
        "caja_u": [round(x, 4) for x in caja["tam"]], "triangulos_visibles": int(sum(p["triangulos"] for p in vis)),
        "piezas_visibles": [p["nodo"] for p in vis], "piezas_ocultas": [p["nodo"] for p in piezas if not p["visible"]],
        "cobertura_px": cobertura, "colores_fuera_de_paleta": fuera, "visibilidad_pedida": visible or {},
        "vistas": [v for v, _, _ in vs], "clip": clip, "t": t, **log,
    }
    refimg = Image.open(ref).convert("RGB") if ref else None
    sub = f"SHA {reporte['sha256'][:12]}… · alto {reporte['alto_u']} u · {reporte['triangulos_visibles']} tris · " \
          f"fuera de paleta: {len(fuera)}"
    hoja = hoja_vertical(paneles, f"CHXP V2 · {nombre}", sub, ref=refimg,
                         paleta=[(n, h) for n, h in usados[:16]], hoja2x2=ref_2x2)
    hoja.save(os.path.join(salida, f"{nombre}_HOJA.png"))
    # GIF
    for g in gifs:
        ig = json.load(open(os.path.join(crudo, f"{nombre}__{g}.json")))
        porvis = {}
        for i in ig["imagenes"]:
            porvis.setdefault(i["t"], {})[i["pasada"]] = i["archivo"]
        cuadros = []
        for tt in sorted(porvis):
            c = _leer(porvis[tt]["color"]); p_ = _leer(porvis[tt]["profundidad"])
            f, _ = componer_imagen(c, p_, ids=decodificar_mascara(_leer(porvis[tt]["mascara"])))
            cuadros.append(Image.fromarray((f * 255).astype(np.uint8)).resize((tam_gif, tam_gif)))
        cuadros[0].save(os.path.join(salida, f"{nombre}_{g}.gif"), save_all=True, append_images=cuadros[1:], duration=70,
                        loop=0)
    reporte["segundos_total"] = round(time.time() - t0, 1)
    reporte["archivos"] = sorted(os.listdir(salida))
    with open(os.path.join(salida, f"{nombre}_REPORTE.json"), "w") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    return reporte


def main():
    ap = argparse.ArgumentParser(description="CHXP V2: render de revisión ALTH con Godot real")
    ap.add_argument("glb")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--silueta", help="GLB de Adán para la silueta a escala")
    ap.add_argument("--ref", help="imagen de referencia (va lado a lado)")
    ap.add_argument("--ref-2x2", action="store_true", help="la referencia es una hoja 2x2: frente, perfil / espalda, 3/4")
    ap.add_argument("--vistas", default="personaje", choices=list(VISTAS))
    ap.add_argument("--visible", default="", help="nodo=1,nodo=0 (piezas intercambiables)")
    ap.add_argument("--clip", default="Idle-loop")
    ap.add_argument("--t", type=float, default=0.0)
    ap.add_argument("--gif", default="", help="clips separados por coma, p. ej. Idle-loop,Walk-loop,Run-loop")
    ap.add_argument("--tam", type=int, default=1024)
    a = ap.parse_args()
    vis = {kv.split("=")[0]: kv.split("=")[1] not in ("0", "no", "false") for kv in a.visible.split(",") if "=" in kv}
    r = render(a.glb, a.salida, silueta=a.silueta, ref=a.ref, vistas=a.vistas, visible=vis, clip=a.clip, t=a.t,
               gifs=[g for g in a.gif.split(",") if g], tam=a.tam, ref_2x2=a.ref_2x2)
    print(json.dumps({k: r[k] for k in ("asset", "alto_u", "triangulos_visibles", "colores_fuera_de_paleta",
                                         "segundos_godot", "segundos_total")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
