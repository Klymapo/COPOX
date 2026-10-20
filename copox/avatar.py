"""crear-avatar · un comando por personaje (19 oct 2026).

  python -m copox.avatar personajes/theo.json [--rapido] [--publicar] [--salida DIR] [--sin-chxp]

La ficha JSON dice TODO el personaje: base (por defecto la congelada), ropa del catálogo + parámetros, colores de la
paleta, telas, pelo, calzado, referencias para CHXP y cómo publicarlo. Pasos: entorno → construir → CHXP V3 → publicar.
Reemplaza la cadena de recetas (V22→V50 + vestir) por: base congelada + ficha.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
import sys

from . import entorno
from .medicion import catalogo

RAIZ = entorno.RAIZ


def _modulos(receta):
    sys.path.insert(0, os.path.join(RAIZ, "docs", "medicion"))
    sys.path.insert(0, RAIZ)
    v3 = importlib.import_module(receta)
    v2 = getattr(v3, "v2", None)
    return {"v3": v3, "v2": v2}


def _visibilidad(f):
    vis = {}
    for clave, tabla in (("pelo", catalogo.PELO), ("calzado", catalogo.CALZADO), ("manos", catalogo.MANOS)):
        if f.get(clave):
            vis.update(tabla[f[clave]])
    vis.update(f.get("visible", {}))
    return vis


def construir(f, dst):
    base = f.get("base") or entorno.BASE
    ropa = catalogo.ROPA[f.get("ropa", {}).get("conjunto", "ninguna")]
    vis = _visibilidad(f)
    if ropa is None:
        from .medicion import rostro_edicion as re
        from .medicion.compactar import compactar
        E = re.Editor(base)
        usados = E.j.setdefault("extensionsUsed", [])
        if "KHR_node_visibility" not in usados:
            usados.append("KHR_node_visibility")
        for n in E.j["nodes"]:
            if n.get("name") in vis:
                ext = n.setdefault("extensions", {})
                if vis[n["name"]]:
                    ext.pop("KHR_node_visibility", None)
                    if not ext:
                        n.pop("extensions")
                else:
                    ext["KHR_node_visibility"] = {"visible": False}
        tmp = dst + ".tmp.glb"
        E.guardar(tmp, nota=f"{f['nombre']} desde ficha (sin ropa).")
        compactar(tmp, dst)
        os.remove(tmp)
        return [{"operacion": "solo visibilidad"}]
    m = _modulos(ropa["receta"])
    respaldo = {}
    try:
        for grupo, params in f["ropa"].get("params", {}).items():
            mod, var = ropa["grupos"][grupo]
            d = getattr(m[mod], var)
            respaldo.setdefault((mod, var), copy.deepcopy(d))
            d.update({k: tuple(v) if isinstance(v, list) else v for k, v in params.items()})
        for clave in ("colores", "telas"):
            if f["ropa"].get(clave):
                mod, var = ropa[clave]
                d = getattr(m[mod], var)
                respaldo.setdefault((mod, var), copy.deepcopy(d))
                d.update(f["ropa"][clave])
        mod, var = ropa["visible"]
        d = getattr(m[mod], var)
        respaldo.setdefault((mod, var), copy.deepcopy(d))
        d.update(vis)
        return m["v3"].main(base, dst)
    finally:
        for (mod, var), d in respaldo.items():          # el catálogo queda como estaba para el siguiente personaje
            getattr(m[mod], var).clear(); getattr(m[mod], var).update(d)


def main():
    ap = argparse.ArgumentParser(description="crear-avatar: ficha JSON → GLB → CHXP V3 → publicar")
    ap.add_argument("ficha")
    ap.add_argument("--salida", default=None)
    ap.add_argument("--rapido", action="store_true", help="CHXP rápido (512 px, sin GIFs)")
    ap.add_argument("--sin-chxp", action="store_true")
    ap.add_argument("--publicar", action="store_true", help="copox-modelos + capturas + ficha + push")
    a = ap.parse_args()
    f = json.load(open(a.ficha))
    entorno.preparar(verificar_base=f.get("base") is None)
    salida = a.salida or os.path.join(os.path.dirname(RAIZ), "build_avatares", f["nombre"].lower())
    os.makedirs(salida, exist_ok=True)
    dst = os.path.join(salida, f["nombre"] + ".glb")
    log = {"construir": construir(f, dst), "glb": dst, "sha256": entorno.sha256(dst)}
    if f.get("sha_esperado"):
        log["sha_igual_al_esperado"] = log["sha256"] == f["sha_esperado"]
    chxp_dir = None
    if not a.sin_chxp:
        from .render import chxp3
        c = f.get("chxp", {})
        chxp_dir = os.path.join(salida, "chxp")
        os.makedirs(chxp_dir, exist_ok=True)
        ref = os.path.join(RAIZ, c["ref"]) if c.get("ref") else None
        rep, aud = chxp3.render(dst, chxp_dir, c.get("tipo", "personaje"), ref=ref, base=f.get("base") or entorno.BASE,
                                brief=c.get("brief"), vistas=c.get("vistas", "personaje"), visible={},
                                gifs=[] if a.rapido else c.get("gif", []), tam=512 if a.rapido else 1024,
                                ref_2x2=c.get("ref_2x2", False), resortes=True)
        log["chxp"] = {"veredicto": aud["veredicto"], "pass": aud["pass"], "fail": aud["fail"],
                       "fallas": [r["id"] for r in aud["revisiones"] if r["veredicto"] == "FAIL"], "dir": chxp_dir}
    if a.publicar:
        from . import publicar
        p = f["publicar"]
        log["publicar"] = publicar.publicar(dst, p["carpeta"], p["nombre"], p["nota"], p.get("estado", "SIN APROBAR"),
                                            p.get("pedido", ""), chxp_dir, push=True)
    print(json.dumps(log, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
