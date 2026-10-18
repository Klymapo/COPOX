"""CLI del renderizador.

  python -m copox.render vistas
  python -m copox.render vista  MODELO.glb "cara_34;modo=arcilla" [-o salida.png] [--autor argos]
  python -m copox.render hoja   MODELO.glb [--modo arcilla] [--tam 512]
  python -m copox.render ref    MODELO.glb "frente" REF.png --recorte 0,40,334,705
  python -m copox.render ab     A.glb B.glb "cara_34;modo=arcilla"
  python -m copox.render servidor [--puerto 8765]      # deja los modelos cargados en memoria

Cualquier orden con --servidor se manda al servidor (más rápido: no recarga el GLB).
Sin -o, la captura va a capturas/AAAA-MM-DD/<modelo>/<autor>/<vista>_<modo>_<tam>.png
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time

import numpy as np

_SESIONES: dict = {}


def sesion(ruta):
    from .sesion import Sesion
    clave = (os.path.abspath(ruta), os.path.getmtime(ruta))
    if clave not in _SESIONES:
        _SESIONES[clave] = Sesion(ruta)
    return _SESIONES[clave]


def ruta_captura(raiz, modelo, autor, nombre):
    return os.path.join(raiz, _dt.date.today().isoformat(), modelo, autor, nombre + ".png")


def _guardar(img, ruta):
    from PIL import Image
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    Image.fromarray(img).save(ruta, optimize=True)
    return ruta


def ejecutar(a: dict) -> dict:
    """Ejecuta una orden (dict) y devuelve un resumen. Lo usan la CLI y el servidor."""
    from .vistas import GUARDADAS, HOJA, leer
    from . import lamina, modos
    t0 = time.time()
    o, autor, raiz = a["orden"], a.get("autor", "elio"), a.get("raiz", "capturas")
    if o == "vistas":
        return {"vistas": {k: v.codigo() for k, v in GUARDADAS.items()}}
    if o == "vista":
        s = sesion(a["modelo"])
        r = s.render(a["codigo"], autor)
        v = r.vista
        sal = a.get("salida") or ruta_captura(raiz, s.nombre, autor, f"{v.nombre}_{v.modo}_{v.tam}")
        r.guardar(sal)
        return {"salida": sal, "segundos_render": round(r.segundos, 3), "codigo": r.codigo}
    if o == "hoja":
        s = sesion(a["modelo"])
        extra = "".join(f";{k}={a[k]}" for k in ("modo", "tam") if a.get(k))
        rs = [s.render(n + extra, autor) for n in a.get("vistas") or HOJA]
        img = np.concatenate([r.imagen for r in rs], 1)
        v = rs[0].vista
        sello = f"{s.nombre} · {s.hash[:8]} · hoja ({', '.join(r.vista.nombre for r in rs)}) · {v.modo} · {v.tam}px · {autor} · {_dt.date.today()}"
        img = modos.sellar(img, sello, rs[0].codigo.replace(f"yaw={v.yaw:g};", ""), t=max(11, v.tam // 40))
        sal = a.get("salida") or ruta_captura(raiz, s.nombre, autor, f"hoja_{v.modo}_{v.tam}")
        return {"salida": _guardar(img, sal), "segundos": round(time.time() - t0, 2)}
    if o == "ref":
        s = sesion(a["modelo"])
        rec = tuple(int(x) for x in a["recorte"].split(",")) if a.get("recorte") else None
        img, info = lamina.lamina_ref(s, a["codigo"], a["ref"], rec, autor, a.get("ancla", "ojos"))
        v = leer(a["codigo"])
        sal = a.get("salida") or ruta_captura(raiz, s.nombre, autor, f"ref_{v.nombre}_{v.modo}_{v.tam}")
        return {"salida": _guardar(img, sal), "iou": info["iou"], "ancla": info["ancla"], "segundos": round(time.time() - t0, 2)}
    if o == "ab":
        sa, sb = sesion(a["modelo"]), sesion(a["modelo_b"])
        img, info = lamina.lamina_ab(sa, sb, a["codigo"], autor)
        v = leer(a["codigo"])
        sal = a.get("salida") or ruta_captura(raiz, sb.nombre, autor, f"ab_{sa.nombre}_{v.nombre}_{v.modo}_{v.tam}")
        return {"salida": _guardar(img, sal), "iou": info["iou"], "segundos": round(time.time() - t0, 2)}
    raise ValueError(f"Orden desconocida: {o}")


def servidor(puerto: int):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                a = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                out, code = ejecutar(a), 200
            except Exception as e:  # el servidor sigue vivo; el error vuelve al cliente
                out, code = {"error": f"{type(e).__name__}: {e}"}, 400
            b = json.dumps(out, ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def log_message(self, *x):
            pass

    print(f"Renderizador COPOX en http://127.0.0.1:{puerto} (Ctrl+C para salir)", flush=True)
    HTTPServer(("127.0.0.1", puerto), H).serve_forever()


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m copox.render", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("vistas")
    q = sub.add_parser("vista"); q.add_argument("modelo"); q.add_argument("codigo")
    q = sub.add_parser("hoja"); q.add_argument("modelo"); q.add_argument("--modo"); q.add_argument("--tam", type=int)
    q.add_argument("--vistas", type=lambda x: x.split(","))
    q = sub.add_parser("ref"); q.add_argument("modelo"); q.add_argument("codigo"); q.add_argument("ref")
    q.add_argument("--recorte"); q.add_argument("--ancla", default="ojos")
    q = sub.add_parser("ab"); q.add_argument("modelo"); q.add_argument("modelo_b"); q.add_argument("codigo")
    q = sub.add_parser("servidor"); q.add_argument("--puerto", type=int, default=8765)
    for n, q in sub.choices.items():
        if n not in ("servidor", "vistas"):
            q.add_argument("-o", "--salida"); q.add_argument("--autor", default="elio")
            q.add_argument("--raiz", default="capturas"); q.add_argument("--servidor", action="store_true")
            q.add_argument("--puerto", type=int, default=8765)
    a = vars(p.parse_args(argv))
    if a["orden"] == "servidor":
        return servidor(a["puerto"])
    for k in ("modelo", "modelo_b", "ref", "salida", "raiz"):
        if a.get(k):
            a[k] = os.path.abspath(a[k])
    if a.pop("servidor", False):
        import urllib.request
        req = urllib.request.Request(f"http://127.0.0.1:{a.pop('puerto')}", json.dumps(a).encode(), {"Content-Type": "application/json"})
        try:
            out = json.loads(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as e:
            out = json.loads(e.read())
    else:
        out = ejecutar(a)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    sys.exit(main())
