"""Adán vestido (derivado de entrega, no versión del cuerpo): V49 + camisa y pantalón ajustados, pies con tenis y pelo
corto. Admin (19 oct 2026): "Entrégame a Adán vestido con la ropa anterior y tenis. También con el pelo nuevo."
Las piezas intercambiables se eligen por visibilidad (KHR_node_visibility): short oculto, pies descalzos ocultos, tenis
visibles, pelo V48.3 oculto, pelo corto visible. La piel tapada por la ropa se quita SOLO en este derivado
(skill vestuario: "culling bajo ropa solo en derivado reversible"); el V49 queda intacto.
Uso: GODOT_BIN=… python vestir_adan.py ADAN_V49.glb ADAN_V49_VESTIDO.glb
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import prueba_ropa_adan as pr  # noqa: E402

VISIBLE = {"CAPA_SHORT": False, "PIES_DESCALZOS": False, "PIES_TENIS": True, "CAPA_GUIA_CAPILAR": False,
           "CAPA_PELO_CORTO": False, "CAPA_PELO_MECHONES": True}


def elegir(E):
    for n in E.j["nodes"]:
        if n.get("name") in VISIBLE:
            ext = n.setdefault("extensions", {})
            if VISIBLE[n["name"]]:
                ext.pop("KHR_node_visibility", None)
                if not ext:
                    n.pop("extensions")
            else:
                ext["KHR_node_visibility"] = {"visible": False}
    return {"operacion": "piezas elegidas", **VISIBLE}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    log = [pr.ropa(E, os.path.dirname(os.path.abspath(dst))), pr.ocultar_bajo_ropa(E), elegir(E)]
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V49 vestido: camisa, pantalón, pies con tenis y pelo corto. Derivado de entrega.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
