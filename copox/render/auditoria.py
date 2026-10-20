"""CHXP V3 · auditoría: SENKU + skills como revisiones con veto (19 oct 2026).

Admin: "integra SENKU a CHXP … incluye todas las skills" → "Revisiones que vetan". Cada revisión devuelve
PASS / FAIL / N-A con su medida y su umbral. Regla COPOX: 100 % de las aplicables en PASS; un FAIL veta; N-A no cuenta.
Las reglas de las skills viven en copox/render/skills_reglas.json (inventario de Drive, ramas de Klymapo y repo):
- las "medibles" que tienen revisión implementada aquí se evalúan (campo `revision`);
- las medibles sin implementar salen como PENDIENTE (visibles, no vetan todavía);
- las de juicio visual salen como checklist para el revisor humano o el agente revisor-visual-alth.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THEO = os.path.join(RAIZ, "assets", "joven_rubio", "theo_alpha.glb")
THEO_SHA = "ed2b04ecd9e22a19794591b873c19c2b30323a9ae836f7dd820134bd0113580b"
# colores fuera de paleta ya aprobados con Adán V30 (interior de boca, ceja horneada, lengua): no vetan
EXCEPCIONES_PALETA = {"BOCA_INTERIOR_NEGRO", "CEJA_BLOQUE", "LENGUA_ALTH"}
UMBRALES = {
    "senku_cabeza": 0.88,       # IoU de la franja de pelo por vista (Theo aprobado: 0.89–0.94)
    "senku_cuerpo": 0.78,       # IoU del cuerpo entero por vista (Theo vestido v1: 0.80–0.86)
    "cobertura_pelo": 0.995,
    "apoyo_mm": 1.5,
    "paleta_de": 6.0,
}
TIPOS = ("personaje", "pelo", "ropa", "calzado", "objeto", "edificio", "animacion")


def _r(id_, veredicto, medida=None, umbral=None, detalle=None, fuente="chxp3"):
    return {"id": id_, "veredicto": veredicto, "medida": medida, "umbral": umbral, "detalle": detalle,
            "fuente": fuente}


# ── revisiones ──────────────────────────────────────────────────────────────────────────────────────────────────────
def rev_theo_protegido(**_):
    if not os.path.exists(THEO):
        return _r("theo_protegido", "N-A", detalle="theo_alpha.glb no está en este checkout")
    sha = hashlib.sha256(open(THEO, "rb").read()).hexdigest()
    return _r("theo_protegido", "PASS" if sha == THEO_SHA else "FAIL", sha[:16], THEO_SHA[:16], fuente="CLAUDE.md")


def rev_apoyo(glb, **_):
    from copox.medicion import senku_ref as sr
    V, _ = sr.malla_visible(glb)
    y0 = float(V[:, 1].min()) * 1000
    return _r("apoyo_piso", "PASS" if abs(y0) <= UMBRALES["apoyo_mm"] else "FAIL", round(y0, 2),
              f"|y_min| ≤ {UMBRALES['apoyo_mm']} mm", fuente="spec/CLAUDE.md: pies en el piso")


def rev_paleta(reporte, **_):
    malos = [c for c in reporte.get("colores_fuera_de_paleta", [])
             if c["material"] not in EXCEPCIONES_PALETA and c["deltaE"] > UMBRALES["paleta_de"]]
    return _r("paleta_alth", "FAIL" if malos else "PASS", len(malos), f"ΔE ≤ {UMBRALES['paleta_de']}",
              [f"{c['material']} {c['color']} (ΔE {c['deltaE']} vs {c['cercano']})" for c in malos],
              fuente="CLAUDE.md: colores solo de la paleta")


def rev_senku(glb, ref, tipo, ocultar=(), salida=None, **_):
    from copox.medicion import senku_ref as sr
    if not ref or not os.path.exists(os.path.splitext(ref)[0] + ".senku.json"):
        return [_r("senku_silueta", "N-A", detalle="sin hoja con .senku.json")]
    out = []
    regiones = ["cabeza"] if tipo == "pelo" else (["objeto", "cabeza"] if tipo in ("personaje", "ropa") else ["objeto"])
    for reg in regiones:
        img = os.path.join(salida, f"senku_{reg}.png") if salida else None
        a = sr.auditar(glb, ref, reg, ocultar, salida=img)
        clave, um = ("pelo", UMBRALES["senku_cabeza"]) if reg == "cabeza" else ("iou", UMBRALES["senku_cuerpo"])
        vals = {v: (a["iou"][v][clave] if isinstance(a["iou"][v], dict) else "N-A") for v in ("frente", "perfil", "espalda")}
        num = [x for x in vals.values() if x != "N-A"]
        ver = "N-A" if not num else ("PASS" if min(num) >= um else "FAIL")
        out.append(_r(f"senku_{reg}", ver, vals, f"≥ {um} por vista", {"avisos": a["avisos"], "imagen": img},
                      fuente="SENKU senku_ref"))
    return out


# Pisos por región (frente y espalda; el perfil sale informativo porque la hoja en T lo deforma). Calibrados el 19 oct
# 2026 sobre Theo V4_1 (variante elegida) menos un margen: son un PISO contra regresiones regionales, no la meta.
# Pies está bajo a propósito: las suelas miden pocos píxeles y el zapato aún difiere de la hoja (ver BITACORA).
PISO_REGIONES = {"cabeza": 0.85, "hombros": 0.68, "torso": 0.75, "piernas": 0.75, "pies": 0.42}


def rev_senku_regiones(glb, ref, tipo, ocultar=(), salida=None, **_):
    from copox.medicion import senku_ref as sr
    if not ref or not os.path.exists(os.path.splitext(ref)[0] + ".senku.json"):
        return _r("senku_regiones", "N-A", detalle="sin hoja con .senku.json")
    img = os.path.join(salida, "senku_regiones.png") if salida else None
    a = sr.auditar(glb, ref, "regiones", ocultar, salida=img)
    med, malas = {}, []
    for v in ("frente", "espalda", "perfil"):
        fila = a["iou"].get(v)
        if not isinstance(fila, dict):
            continue
        for reg, piso in PISO_REGIONES.items():
            x = fila.get(reg)
            med[f"{v}.{reg}"] = x
            if v != "perfil" and x is not None and x < piso:
                malas.append(f"{reg} en {v}: {x} < {piso}")
    return _r("senku_regiones", "FAIL" if malas else "PASS", med, "piso por región en frente/espalda (perfil informativo)",
              malas or {"imagen": img}, fuente="SENKU senku_ref (regiones)")


def rev_cobertura_pelo(glb, **_):
    """Desde el GLB: el área de pelo es la de la guía capilar (CAPA_GUIA_CAPILAR); cada dirección desde el centro de la
    cabeza debe tocar el pelo visible (o piel al nivel del pelo: oreja, cara)."""
    from copox.medicion.gltf import Modelo
    from copox.medicion.pelo_cobertura import _choca, MINIMO
    M = Modelo(glb)
    guia, pelo, piel = [], [], []
    for p in M.prims:
        nd = M.j["nodes"][p.nodo]
        nombre = nd.get("name", "")
        vis = nd.get("extensions", {}).get("KHR_node_visibility", {}).get("visible", True)
        tri = p.pos[p.indices]
        if nombre == "CAPA_GUIA_CAPILAR":
            guia.append(p.pos)
        elif vis and "PELO" in nombre.upper():
            pelo.append(tri)
        elif vis and "PIEL" in p.material.get("name", "").upper():
            piel.append(tri)
    if not guia or not pelo:
        return _r("cobertura_pelo", "N-A", detalle="sin guía capilar o sin pelo visible")
    G = np.vstack(guia)
    c = G.mean(0) * [0, 1, 1] + [0, -0.02, 0]
    D = G - c; R = np.linalg.norm(D, axis=1); D /= R[:, None]
    k = np.random.default_rng(0).choice(len(D), min(2500, len(D)), replace=False)
    D, R = D[k], R[k]
    Tp = np.vstack(pelo)
    Vp, Tp_ = Tp.reshape(-1, 3), np.arange(len(Tp) * 3).reshape(-1, 3)
    th = _choca(c, D, Vp, Tp_, distancia=True)
    ok = np.isfinite(th)
    if piel:
        Ts = np.vstack(piel)
        Ts = Ts[(Ts[:, :, 1] > 0.47).all(1)]
        ts = _choca(c, D, Ts.reshape(-1, 3), np.arange(len(Ts) * 3).reshape(-1, 3), distancia=True)
        ok = (th >= ts) | (np.isfinite(ts) & (ts >= R - 0.004))
    f = float(ok.mean())
    return _r("cobertura_pelo", "PASS" if f >= MINIMO else "FAIL", round(f, 4), f"≥ {MINIMO}",
              fuente="Admin 19 oct: cubrir siempre toda el área de pelo")


def rev_resortes(glb, **_):
    from copox.medicion.gltf import leer_glb
    j, _b = leer_glb(glb)
    nombres_j = {j["nodes"][k]["name"] for s in j.get("skins", []) for k in s["joints"]}
    pelo = [n for n in j["nodes"] if "PELO" in n.get("name", "").upper() and "mesh" in n
            and n.get("extensions", {}).get("KHR_node_visibility", {}).get("visible", True)]
    if not pelo:
        return _r("pelo_resortes", "N-A", detalle="sin pelo visible")
    faltan = []
    for n in pelo:
        cfg = n.get("extras", {}).get("resortes")
        if not cfg:
            faltan.append(f"{n['name']}: sin resortes")
            continue
        for cad in cfg["cadenas"]:
            faltan += [f"{n['name']}: {b} no está en el esqueleto" for b in cad if b not in nombres_j]
    return _r("pelo_resortes", "FAIL" if faltan else "PASS", len(pelo), "pelo visible con cadenas válidas", faltan,
              fuente="Admin 19 oct: que se mueva como pelo")



def _prims_glb(glb):
    from copox.medicion.gltf import leer_glb, accesor
    j, b = leer_glb(glb)
    out = []
    for ni, n in enumerate(j["nodes"]):
        if "mesh" not in n:
            continue
        vis = n.get("extensions", {}).get("KHR_node_visibility", {}).get("visible", True)
        for p in j["meshes"][n["mesh"]]["primitives"]:
            out.append((n.get("name", ""), vis, p))
    return j, b, accesor, out


def _nuevas(base):
    """(nodo, material) presentes en la base: con --base, las revisiones de malla miran SOLO lo nuevo (lo que el asset
    agrega); la deuda de la base se reporta aparte (skills regional-model-auditor: 'vecino_nuevo_defecto')."""
    if not base or not os.path.exists(base):
        return None
    j, b, acc, prims = _prims_glb(base)
    return {(n, j["materials"][p.get("material", 0)]["name"]) for n, _v, p in prims}


def _clave(j, n, p):
    return (n, j["materials"][p.get("material", 0)]["name"])


def rev_integridad(glb, **_):
    """gltf-rig-guardian / copox-auditoria-3d: índices en rango, sin NaN, sin primitivas vacías, IBM finitas."""
    j, b, acc, prims = _prims_glb(glb)
    malos = []
    for nombre, _v, p in prims:
        if "indices" not in p:
            continue
        I = acc(j, b, p["indices"]).ravel()
        V = acc(j, b, p["attributes"]["POSITION"])
        if len(I) == 0:
            malos.append(f"{nombre}: primitiva vacía")
        elif I.max() >= len(V):
            malos.append(f"{nombre}: índice fuera de rango")
        if not np.isfinite(V).all():
            malos.append(f"{nombre}: NaN/inf en POSITION")
        if "WEIGHTS_0" in p["attributes"] and not np.isfinite(acc(j, b, p["attributes"]["WEIGHTS_0"])).all():
            malos.append(f"{nombre}: pesos no finitos")
    for s in j.get("skins", []):
        if not np.isfinite(acc(j, b, s["inverseBindMatrices"])).all():
            malos.append("IBM no finitas")
    return _r("integridad_gltf", "FAIL" if malos else "PASS", len(malos), 0, malos[:10],
              fuente="gltf-rig-guardian, copox-auditoria-3d")


def rev_pesos(glb, **_):
    j, b, acc, prims = _prims_glb(glb)
    peor = 0.0
    for nombre, _v, p in prims:
        if "WEIGHTS_0" in p["attributes"]:
            W = acc(j, b, p["attributes"]["WEIGHTS_0"]).astype(float)
            if W.dtype.kind != "f" or W.max() > 1.5:
                W = W / 255.0
            peor = max(peor, float(np.abs(W.sum(1) - 1).max()))
    return _r("pesos_normalizados", "PASS" if peor < 0.01 else "FAIL", round(peor, 5), "|Σw − 1| < 0.01",
              fuente="vestuario.pesos_normalizados, rig.pesos_normalizados")


def rev_dedos(glb, **_):
    from copox.medicion.gltf import leer_glb
    j, _b = leer_glb(glb)
    nombres = {j["nodes"][k]["name"] for s in j.get("skins", []) for k in s["joints"]}
    if not nombres:
        return _r("cinco_dedos", "N-A", detalle="sin esqueleto")
    cuenta = {lado: sum(1 for n in nombres if n.startswith(lado) and any(d in n for d in
              ("Thumb", "Index", "Middle", "Ring", "Little"))) for lado in ("Left", "Right")}
    ok = all(v == 15 for v in cuenta.values())
    return _r("cinco_dedos", "PASS" if ok else "FAIL", cuenta, "15 huesos de dedo por mano", fuente="rig.cinco_dedos")


def rev_preservado(glb, base=None, **_):
    """rig.sin_perdida_clips_targets / ra.clips_preservados: lo que la base trae (clips, huesos, morphs) sigue ahí."""
    if not base or not os.path.exists(base):
        return _r("base_preservada", "N-A", detalle="sin --base")
    from copox.medicion.gltf import leer_glb
    ja, _ = leer_glb(base); jb, _ = leer_glb(glb)
    clips_a = {a.get("name") for a in ja.get("animations", [])}; clips_b = {a.get("name") for a in jb.get("animations", [])}
    hues_a = {ja["nodes"][k]["name"] for s in ja.get("skins", []) for k in s["joints"]}
    hues_b = {jb["nodes"][k]["name"] for s in jb.get("skins", []) for k in s["joints"]}
    morph = lambda j: max((len(p.get("targets", [])) for m in j["meshes"] for p in m["primitives"]), default=0)  # noqa: E731
    faltan = sorted(clips_a - clips_b)[:10] + sorted(hues_a - hues_b)[:10]
    if morph(jb) < morph(ja):
        faltan.append(f"morphs {morph(jb)} < {morph(ja)}")
    return _r("base_preservada", "FAIL" if faltan else "PASS", {"clips": len(clips_b), "huesos": len(hues_b)},
              "nada de la base se pierde", faltan, fuente="rig.sin_perdida_clips_targets, ra.clips_preservados")


def rev_degenerados(glb, base=None, **_):
    j, b, acc, prims = _prims_glb(glb)
    viejas = _nuevas(base) or set()
    tot = mal = 0
    for nombre, vis, p in prims:
        if not vis or "indices" not in p or _clave(j, nombre, p) in viejas:
            continue
        V = acc(j, b, p["attributes"]["POSITION"]).astype(float); T = acc(j, b, p["indices"]).reshape(-1, 3)
        a = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1) / 2
        tot += len(T); mal += int((a < 1e-10).sum())
    f = mal / max(tot, 1)
    return _r("areas_degeneradas", "PASS" if f < 0.005 else "FAIL", round(f, 5), "< 0.5 % de triángulos" +
              (" (solo piezas nuevas sobre la base)" if viejas else ""),
              fuente="aud.areas_degeneradas, saf.no_degenerados_winding")


def rev_normales(glb, base=None, **_):
    """aud.normales / vestuario.normales_no_invertidas: la normal guardada concuerda con el sentido de la cara."""
    j, b, acc, prims = _prims_glb(glb)
    viejas = _nuevas(base) or set()
    peor = []
    for nombre, vis, p in prims:
        if not vis or "indices" not in p or "NORMAL" not in p["attributes"] or _clave(j, nombre, p) in viejas:
            continue
        V = acc(j, b, p["attributes"]["POSITION"]).astype(float); N = acc(j, b, p["attributes"]["NORMAL"]).astype(float)
        T = acc(j, b, p["indices"]).reshape(-1, 3)
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        f = float((np.einsum("ij,ij->i", fn, N[T].mean(1)) < 0).mean())
        if f > 0.02:
            peor.append(f"{nombre}/{j['materials'][p.get('material', 0)]['name']}: {f:.1%}")
    return _r("normales", "FAIL" if peor else "PASS", len(peor), "≤ 2 % de caras invertidas por primitiva", peor[:10],
              fuente="aud.normales, vestuario.normales_no_invertidas")


def rev_flotantes(glb, base=None, **_):
    """asset.sin_flotantes: cada primitiva visible (nueva, si hay base) toca (≤ 3 mm) alguna otra."""
    from scipy.spatial import cKDTree
    j, b, acc, prims = _prims_glb(glb)
    viejas = _nuevas(base) or set()
    Ps = [(f"{n}/{j['materials'][p.get('material', 0)]['name']}", acc(j, b, p["attributes"]["POSITION"]).astype(float),
           _clave(j, n, p) not in viejas) for n, vis, p in prims if vis and "indices" in p]
    if len(Ps) < 2:
        return _r("sin_flotantes", "N-A", detalle="una sola pieza")
    sueltas = []
    for i, (nom, P, nueva) in enumerate(Ps):
        if not nueva:
            continue
        resto = np.vstack([Q for k, (_, Q, _n) in enumerate(Ps) if k != i])
        d, _ = cKDTree(resto).query(P[:: max(1, len(P) // 2000)])
        if d.min() > 0.006:          # entre VÉRTICES: las piezas low-poly tienen vértices a ~3–5 mm aunque se toquen
            sueltas.append(f"{nom}: {d.min() * 1000:.1f} mm")
    return _r("sin_flotantes", "FAIL" if sueltas else "PASS", len(sueltas), "0 piezas a más de 6 mm (vértice a vértice)", sueltas,
              fuente="asset.sin_flotantes")


def rev_triangulos(glb, tipo, reporte, clase=None, **_):
    """asset.triangulos: tope de la spec (geometria.tris_max). Personaje: principal 160000 / ciudadano 60000 (Admin,
    19 oct 2026). Se cuentan los triángulos visibles."""
    tm = json.load(open(os.path.join(RAIZ, "spec", "alth_spec.json")))["geometria"]["tris_max"]
    clave = clase or {"personaje": "personaje_principal", "objeto": "mueble", "ropa": "personaje_principal",
                      "pelo": "personaje_principal", "calzado": "personaje_principal"}.get(tipo)
    tope, n = tm.get(clave), reporte.get("triangulos_visibles")
    if tope is None or n is None:
        return _r("triangulos_tope", "N-A")
    return _r("triangulos_tope", "PASS" if n <= tope else "FAIL", n, f"≤ {tope} ({clave})", fuente="asset.triangulos")

def rev_brief(brief=None, **_):
    """CLAUDE.md: técnica geométrica nueva sin research brief → RESEARCH_REQUIRED (skill investigar-referencias)."""
    if not brief:
        return _r("research_brief", "N-A", detalle="sin tema declarado (--brief)")
    temas = [t for t in str(brief).split(",") if t]
    faltan = []
    for t in temas:
        p = os.path.join(RAIZ, "docs", "investigacion", f"{t}.md")
        if not os.path.exists(p) or "Brief válido: sí" not in open(p).read():
            faltan.append(t)
    return _r("research_brief", "FAIL" if faltan else "PASS", temas, "brief válido por tema",
              ["RESEARCH_REQUIRED: " + t for t in faltan], fuente="CLAUDE.md, skill investigar-referencias")


def _dentro_por_paridad(Q, V, T, d=np.array([0.31, 0.94, 0.13])):
    """Punto dentro de una malla cerrada: número impar de cruces de un rayo."""
    d = d / np.linalg.norm(d)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = B - A, C - A
    p = np.cross(d, e2); det = (p * e1).sum(1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    q1 = np.cross(e1, d)
    out = np.zeros(len(Q), bool)
    for k in range(0, len(Q), 64):
        s_ = Q[k:k + 64, None, :] - A[None]
        u = (s_ * p[None]).sum(2) * inv
        q = np.cross(s_, e1[None])
        v = (q * d).sum(2) * inv
        t = (q * e2[None]).sum(2) * inv
        n = (ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-7)).sum(1)
        out[k:k + 64] = n % 2 == 1
    return out


def _cerrada(T, V=None):
    if V is not None:                                  # mallas facetadas: soldar por posición
        _, inv = np.unique(np.round(V, 6), axis=0, return_inverse=True)
        T = inv.ravel()[T]
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    _, c = np.unique(e, axis=0, return_counts=True)
    return bool((c == 2).all())


POSES = ((None, 0.0), ("Walk-loop", 0.25), ("Walk-loop", 0.75), ("Run-loop", 0.3), ("Sit-pose", 0.5))
PARES = (("piel", "CAPA_CAMISA"), ("CAPA_CAMISA", "CAPA_CHALECO"), ("piel", "CAPA_PANTALON"),
         ("PIES_ZAPATO", "CAPA_PANTALON"))


def _grupos(M):
    g = {}
    for i, p in enumerate(M.prims):
        nd = M.j["nodes"][p.nodo]
        if not nd.get("extensions", {}).get("KHR_node_visibility", {}).get("visible", True):
            continue
        nombre = nd.get("name", "")
        clave = "piel" if "PIEL" in p.material.get("name", "").upper() and nombre == "ADAN_CUERPO" else nombre
        g.setdefault(clave, []).append(i)
    return g


def rev_capas(glb, umbral=0.01, tol=0.0015, **_):
    """Ropa por capas (skills vestuario.sin_clipping_poses_extremas, cloth.clipping_transiciones): en reposo, Walk,
    Run y Sit la capa de afuera no queda dentro de la de abajo. Por cada vértice de afuera cerca (< 1 cm) de la de
    abajo: distancia con signo sobre la normal de la de abajo; penetra si < −tol. FAIL si > 1 % en algún par/pose."""
    from scipy.spatial import cKDTree
    from copox.medicion.gltf import Modelo
    M = Modelo(glb)
    g = _grupos(M)
    pares = [(a, b) for a, b in PARES if a in g and b in g]
    if not pares:
        return _r("capas_sin_atravesar", "N-A", detalle="sin prendas por capas")
    peor, detalle = 0.0, []
    for clip, fr in POSES:
        if clip and clip not in M.clips and clip.replace("-loop", "") not in M.clips:
            continue
        pos = M.posar(clip, fr) if clip else M.posar(None, 0.0)
        for a, b in pares:
            Va = np.vstack([pos[i] for i in g[a]])
            Ta = np.vstack([M.prims[i].indices + sum(len(pos[k]) for k in g[a][:n]) for n, i in enumerate(g[a])])
            fn = np.cross(Va[Ta[:, 1]] - Va[Ta[:, 0]], Va[Ta[:, 2]] - Va[Ta[:, 0]])
            Na = np.zeros_like(Va)
            for c in range(3):
                np.add.at(Na, Ta[:, c], fn)
            Na /= np.maximum(np.linalg.norm(Na, axis=1, keepdims=True), 1e-12)
            Vb = np.vstack([pos[i] for i in g[b]])
            Tb = np.vstack([M.prims[i].indices + sum(len(pos[k]) for k in g[b][:n]) for n, i in enumerate(g[b])])
            fb = np.cross(Vb[Tb[:, 1]] - Vb[Tb[:, 0]], Vb[Tb[:, 2]] - Vb[Tb[:, 0]])
            Nb = np.zeros_like(Vb)
            for c in range(3):
                np.add.at(Nb, Tb[:, c], fb)
            Nb /= np.maximum(np.linalg.norm(Nb, axis=1, keepdims=True), 1e-12)
            sel = np.ones(len(Vb), bool)
            if b == "CAPA_PANTALON" and a == "PIES_ZAPATO":
                sel &= Vb[:, 1] < 0.12
            d, j = cKDTree(Va).query(Vb, distance_upper_bound=0.01)
            # solo la cara de AFUERA de la prenda (las paredes de los cortes van hacia adentro, ocultas, a propósito)
            cerca = np.isfinite(d) & sel
            cerca[cerca] &= np.einsum("ij,ij->i", Nb[cerca], Na[j[cerca]]) > 0.5
            if not cerca.any():
                continue
            s_ = np.einsum("ij,ij->i", Vb[cerca] - Va[j[cerca]], Na[j[cerca]])
            sosp = s_ < -tol
            # si la capa de abajo es cerrada (zapato), se confirma con paridad de rayo: la normal del vértice más
            # cercano engaña junto a las aristas
            if sosp.any() and all(_cerrada(M.prims[i].indices, M.prims[i].pos) for i in g[a]):
                Qs = Vb[cerca][sosp]
                conf = np.zeros(len(Qs), bool)
                o = 0
                for i in g[a]:
                    conf |= _dentro_por_paridad(Qs, pos[i], M.prims[i].indices)
                sosp[np.nonzero(sosp)[0][~conf]] = False
            f = float(sosp.mean())
            if f > peor:
                peor = f
            if f > umbral:
                detalle.append(f"{b} dentro de {a} en {clip or 'reposo'} {fr}: {f:.1%}")
    # Desde el 19 oct 2026 es INFORMATIVA (no veta): cuenta paredes ocultas (cuello, cortes) que nadie ve. La compuerta
    # que veta es capas_visibles (lo que se ve en el render). Se conserva la medida para diagnóstico.
    return _r("capas_sin_atravesar", "N-A", round(peor, 4), f"informativa (≤ {umbral:.0%} por par y pose); veta capas_visibles",
              detalle[:10], fuente="vestuario.sin_clipping_poses_extremas, cloth.clipping_transiciones")


VISTAS_CAPAS = (0.0, 90.0, 180.0, 270.0, 35.0, -35.0)      # frente, lado, espalda, lado, 3/4 y 3/4
PARES_VISIBLES = (("piel", "CAPA_CAMISA"), ("CAPA_CAMISA", "CAPA_CHALECO"), ("piel", "CAPA_PANTALON"),
                  ("CAPA_CAMISA", "CAPA_PANTALON"))


def rev_capas_visibles(glb, umbral=0.01, gap=0.006, px=420, **_):
    """Lo que SE VE (Admin, 19 oct: la prueba geométrica reprobaba por paredes ocultas). Se rasteriza el modelo
    posado (reposo, Walk, Run, Sit) desde 6 vistas. Un píxel es 'atravesado' si lo primero que se ve es la capa de
    ABAJO (p. ej. piel o camisa) y, quitándola, justo detrás (< 6 mm) está la capa de ARRIBA (camisa, chaleco,
    pantalón): la de abajo se asoma a través de la de arriba. Medida: píxeles atravesados / píxeles visibles de la capa
    de arriba, por par y pose (sumando vistas). FAIL si > 1 %."""
    from copox.medicion.gltf import Modelo
    from copox.render.raster import rasterizar
    M = Modelo(glb)
    g = _grupos(M)
    pares = [(a, b) for a, b in PARES_VISIBLES if a in g and b in g]
    if not pares:
        return _r("capas_visibles", "N-A", detalle="sin prendas por capas")
    nombres = sorted(g)
    gid = {n: i for i, n in enumerate(nombres)}
    peor, detalle, medidas = 0.0, [], {}
    for clip, fr in POSES:
        if clip and clip not in M.clips and clip.replace("-loop", "") not in M.clips:
            continue
        pos = M.posar(clip, fr) if clip else M.posar(None, 0.0)
        Vs, Ts, Gs, o = [], [], [], 0
        for n in nombres:
            for i in g[n]:
                Vs.append(pos[i]); Ts.append(M.prims[i].indices + o); Gs.append(np.full(len(M.prims[i].indices), gid[n]))
                o += len(pos[i])
        V, T, G = np.vstack(Vs), np.vstack(Ts), np.concatenate(Gs)
        lo, hi = V.min(0), V.max(0)
        c = (lo + hi) / 2
        esc = (px - 20) / max(hi[1] - lo[1], np.hypot(hi[0] - lo[0], hi[2] - lo[2]))
        cuenta = {(a, b): [0, 0] for a, b in pares}
        for ang in VISTAS_CAPAS:
            r = np.radians(ang)
            x = (V[:, 0] - c[0]) * np.cos(r) + (V[:, 2] - c[2]) * np.sin(r)
            z = -(V[:, 0] - c[0]) * np.sin(r) + (V[:, 2] - c[2]) * np.cos(r)
            X = (x * esc + px / 2)[T]; Y = ((c[1] - V[:, 1]) * esc + px / 2)[T]; Z = z[T]

            def capa(sin=None):
                sel = np.ones(len(T), bool) if sin is None else G != gid[sin]
                idx = np.nonzero(sel)[0]
                tri, _, prof = rasterizar(X[idx], Y[idx], Z[idx], (px, px))
                tri = tri.ravel(); prof = prof.ravel()
                lab = np.where(tri >= 0, G[idx][np.maximum(tri, 0)], -1)
                return lab, prof
            lab, prof = capa()
            for a in {a for a, _ in pares}:
                lab2, prof2 = capa(sin=a)
                for (a_, b) in pares:
                    if a_ != a:
                        continue
                    with np.errstate(invalid="ignore"):
                        cruza = (lab == gid[a]) & (lab2 == gid[b]) & (prof - prof2 < gap)
                    cuenta[(a, b)][0] += int(cruza.sum())
                    cuenta[(a, b)][1] += int((lab == gid[b]).sum() + cruza.sum())
        for (a, b), (n_, d_) in cuenta.items():
            f = n_ / max(d_, 1)
            medidas[f"{b}/{a}@{clip or 'reposo'}"] = round(f, 4)
            peor = max(peor, f)
            if f > umbral:
                detalle.append(f"{a} se asoma por {b} en {clip or 'reposo'} {fr}: {f:.1%} de lo visible")
    return _r("capas_visibles", "FAIL" if detalle else "PASS", round(peor, 4), f"≤ {umbral:.0%} de lo visible por par y pose",
              detalle[:10] or None, fuente="Admin 19 oct 2026, vestuario.sin_clipping_poses_extremas (render)")


def _nodo_mundo(j, nombre):
    ns = j["nodes"]
    padre = {c: i for i, n in enumerate(ns) for c in n.get("children", [])}

    def mat(n):
        if "matrix" in n:
            return np.array(n["matrix"], float).reshape(4, 4).T
        t = np.array(n.get("translation", [0, 0, 0]), float); x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        s = np.array(n.get("scale", [1, 1, 1]), float)
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m = np.eye(4); m[:3, :3] = R * s; m[:3, 3] = t
        return m
    i = next((k for k, n in enumerate(ns) if n.get("name") == nombre), None)
    if i is None:
        return None
    m = mat(ns[i])
    while i in padre:
        i = padre[i]; m = mat(ns[i]) @ m
    return m[:3, 3]


def rev_hombro(glb, umbral=0.97, **_):
    """Admin (19 oct 2026): "sigo viendo los hombros blancos". La cara de afuera de la camisa ARRIBA del hombro
    (entre el cuello y la esquina del hombro = articulación del brazo, sobre la línea de la axila) debe quedar cubierta
    por el chaleco: el rayo que sale por su normal choca con el chaleco antes de 12 mm. Reposo. N-A si no hay chaleco y camisa."""
    from copox.medicion.gltf import Modelo
    M = Modelo(glb)
    g = _grupos(M)
    if "CAPA_CAMISA" not in g or "CAPA_CHALECO" not in g:
        return _r("hombro_cubierto", "N-A", detalle="sin camisa + chaleco")
    pos = M.posar(None, 0.0)
    art = [_nodo_mundo(M.j, n) for n in ("LeftUpperArm", "RightUpperArm")]
    if any(a is None for a in art):
        return _r("hombro_cubierto", "N-A", detalle="rig sin UpperArm")
    hx, hy = float(np.mean([abs(a[0]) for a in art])), float(np.mean([a[1] for a in art]))
    Vc = np.vstack([pos[i] for i in g["CAPA_CAMISA"]])
    Tc = np.vstack([M.prims[i].indices + sum(len(pos[k]) for k in g["CAPA_CAMISA"][:n])
                    for n, i in enumerate(g["CAPA_CAMISA"])])
    fn = np.cross(Vc[Tc[:, 1]] - Vc[Tc[:, 0]], Vc[Tc[:, 2]] - Vc[Tc[:, 0]])
    Nc = np.zeros_like(Vc)
    for c in range(3):
        np.add.at(Nc, Tc[:, c], fn)
    Nc /= np.maximum(np.linalg.norm(Nc, axis=1, keepdims=True), 1e-12)
    x = np.abs(Vc[:, 0])
    sel = (x > 0.050) & (x < hx - 0.004) & (Vc[:, 1] > hy - 0.005) & (Nc[:, 1] > 0.3)
    if not sel.any():
        return _r("hombro_cubierto", "N-A", detalle="sin cara de hombro en la camisa")
    Vv = np.vstack([pos[i] for i in g["CAPA_CHALECO"]])
    Tv = np.vstack([M.prims[i].indices + sum(len(pos[k]) for k in g["CAPA_CHALECO"][:n])
                    for n, i in enumerate(g["CAPA_CHALECO"])])
    # rayo desde la camisa hacia afuera (su normal): ¿choca con el chaleco antes de 12 mm?
    Q, D = Vc[sel] + Nc[sel] * 1e-5, Nc[sel]
    A, B, C = Vv[Tv[:, 0]], Vv[Tv[:, 1]], Vv[Tv[:, 2]]
    e1, e2 = B - A, C - A
    ok = np.zeros(len(Q), bool)
    for k in range(0, len(Q), 32):
        q, dd = Q[k:k + 32, None, :], D[k:k + 32, None, :]
        p_ = np.cross(dd, e2[None]); det = (p_ * e1[None]).sum(2)
        inv = np.where(np.abs(det) > 1e-14, 1 / np.where(np.abs(det) > 1e-14, det, 1), 0)
        s_ = q - A[None]
        u = (s_ * p_).sum(2) * inv
        qq = np.cross(s_, e1[None])
        v = (qq * dd).sum(2) * inv
        t = (qq * e2[None]).sum(2) * inv
        ok[k:k + 32] = ((inv != 0) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < 0.012)).any(1)
    f = float(ok.mean())
    return _r("hombro_cubierto", "PASS" if f >= umbral else "FAIL", round(f, 4), f"≥ {umbral:.0%} de la camisa del hombro",
              None if f >= umbral else [f"{int((~ok).sum())} vértices de camisa sin chaleco encima (x<{hx:.3f}, y>{hy - 0.005:.3f})"],
              fuente="Admin 19 oct 2026, vestuario.capas")


def deuda_base(base):
    """Lo que la base ya trae mal (no veta al asset; se reporta para arreglarlo en el cuerpo)."""
    if not base or not os.path.exists(base):
        return []
    return [r for r in (rev_degenerados(base), rev_normales(base), rev_flotantes(base)) if r["veredicto"] == "FAIL"]


REVISIONES = {
    "theo_protegido": (rev_theo_protegido, TIPOS),
    "apoyo_piso": (rev_apoyo, ("personaje", "calzado", "objeto", "edificio")),
    "paleta_alth": (rev_paleta, TIPOS),
    "senku": (rev_senku, ("personaje", "pelo", "ropa", "objeto", "edificio")),
    "senku_regiones": (rev_senku_regiones, ("personaje", "ropa")),
    "cobertura_pelo": (rev_cobertura_pelo, ("personaje", "pelo")),
    "pelo_resortes": (rev_resortes, ("personaje", "pelo")),
    "integridad_gltf": (rev_integridad, TIPOS),
    "research_brief": (rev_brief, TIPOS),
    "capas_sin_atravesar": (rev_capas, ("personaje", "ropa")),
    "capas_visibles": (rev_capas_visibles, ("personaje", "ropa")),
    "hombro_cubierto": (rev_hombro, ("personaje", "ropa")),
    "pesos_normalizados": (rev_pesos, ("personaje", "pelo", "ropa", "calzado", "animacion")),
    "cinco_dedos": (rev_dedos, ("personaje", "animacion")),
    "base_preservada": (rev_preservado, ("personaje", "pelo", "ropa", "calzado", "animacion")),
    "areas_degeneradas": (rev_degenerados, TIPOS),
    "normales": (rev_normales, TIPOS),
    "sin_flotantes": (rev_flotantes, ("personaje", "objeto", "edificio")),
    "triangulos_tope": (rev_triangulos, ("personaje", "objeto", "pelo", "ropa", "calzado")),
}


def reglas_skills(tipo):
    p = os.path.join(os.path.dirname(__file__), "skills_reglas.json")
    if not os.path.exists(p):
        return [], []
    data = json.load(open(p))
    pend, check = [], []
    hechas = set(REVISIONES) | {"senku_objeto", "senku_cabeza"}
    for s in data.get("skills", []):
        for r in s.get("reglas", []):
            aplica = r.get("aplica_a", ["todos"])
            if "todos" not in aplica and tipo not in aplica:
                continue
            fila = {"skill": s.get("nombre"), "id": r.get("id"), "texto": r.get("texto"), "umbral": r.get("umbral"),
                    "revision": r.get("revision")}
            if r.get("tipo") == "medible":
                if r.get("revision") not in hechas:
                    pend.append(fila)
            else:
                check.append(fila)
    return pend, check


def auditar(glb, tipo, reporte, ref=None, ocultar=(), salida=None, base=None, brief=None):
    filas = []
    for nombre, (f, tipos) in REVISIONES.items():
        if tipo not in tipos:
            continue
        r = f(glb=glb, ref=ref, tipo=tipo, ocultar=ocultar, salida=salida, reporte=reporte, base=base, brief=brief)
        filas += r if isinstance(r, list) else [r]
    pend, check = reglas_skills(tipo)
    aplic = [f for f in filas if f["veredicto"] != "N-A"]
    veredicto = "PASS" if aplic and all(f["veredicto"] == "PASS" for f in aplic) else ("FAIL" if aplic else "N-A")
    return {"tipo": tipo, "veredicto": veredicto, "revisiones": filas, "deuda_base": deuda_base(base),
            "pass": sum(f["veredicto"] == "PASS" for f in filas), "fail": sum(f["veredicto"] == "FAIL" for f in filas),
            "na": sum(f["veredicto"] == "N-A" for f in filas), "pendientes_skills": pend, "checklist_skills": check}
