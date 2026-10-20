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
        if d.min() > 0.003:
            sueltas.append(f"{nom}: {d.min() * 1000:.1f} mm")
    return _r("sin_flotantes", "FAIL" if sueltas else "PASS", len(sueltas), "0 piezas a más de 3 mm", sueltas,
              fuente="asset.sin_flotantes")


def rev_triangulos(glb, tipo, reporte, **_):
    """asset.triangulos (spec): se MIDE y se reporta; el veto queda suspendido hasta que Admin decida (los cuerpos
    aprobados de Adán ya superan el tope de 6000 de la spec)."""
    tope = {"personaje": 6000, "objeto": 1500}.get(tipo)
    n = reporte.get("triangulos_visibles")
    if tope is None or n is None:
        return _r("triangulos_tope", "N-A")
    return _r("triangulos_tope", "N-A", n, f"≤ {tope} (spec)",
              "VETO SUSPENDIDO: contradicción entre la spec y Adán aprobado; decisión de Admin", fuente="asset.triangulos")

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
    "cobertura_pelo": (rev_cobertura_pelo, ("personaje", "pelo")),
    "pelo_resortes": (rev_resortes, ("personaje", "pelo")),
    "integridad_gltf": (rev_integridad, TIPOS),
    "pesos_normalizados": (rev_pesos, ("personaje", "pelo", "ropa", "calzado", "animacion")),
    "cinco_dedos": (rev_dedos, ("personaje", "animacion")),
    "base_preservada": (rev_preservado, ("personaje", "pelo", "ropa", "calzado", "animacion")),
    "areas_degeneradas": (rev_degenerados, TIPOS),
    "normales": (rev_normales, TIPOS),
    "sin_flotantes": (rev_flotantes, ("personaje", "objeto", "edificio")),
    "triangulos_tope": (rev_triangulos, ("personaje", "objeto")),
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


def auditar(glb, tipo, reporte, ref=None, ocultar=(), salida=None, base=None):
    filas = []
    for nombre, (f, tipos) in REVISIONES.items():
        if tipo not in tipos:
            continue
        r = f(glb=glb, ref=ref, tipo=tipo, ocultar=ocultar, salida=salida, reporte=reporte, base=base)
        filas += r if isinstance(r, list) else [r]
    pend, check = reglas_skills(tipo)
    aplic = [f for f in filas if f["veredicto"] != "N-A"]
    veredicto = "PASS" if aplic and all(f["veredicto"] == "PASS" for f in aplic) else ("FAIL" if aplic else "N-A")
    return {"tipo": tipo, "veredicto": veredicto, "revisiones": filas, "deuda_base": deuda_base(base),
            "pass": sum(f["veredicto"] == "PASS" for f in filas), "fail": sum(f["veredicto"] == "FAIL" for f in filas),
            "na": sum(f["veredicto"] == "N-A" for f in filas), "pendientes_skills": pend, "checklist_skills": check}
