"""Adán V43.1 (sobre V43): una sola mano visible por defecto.

Pedido de Admin (18 oct 2026): las manos "se ven dobles, encimadas sobre sí mismas".
Desde V40 cada mano trae tres mallas en el mismo lugar (MANO_ABIERTA, MANO_PUNO, MANO_SENALAR) y el controlador del
juego (copox/godot/movimiento/controlador_adan.gd) prende una según el clip. En el archivo las tres venían visibles,
así que todo lo que no usa ese controlador (CHXP, el banco de pruebas de Godot, Blender) las dibujaba juntas.
Cambio: puño y señalar quedan ocultos por defecto con la extensión estándar KHR_node_visibility (Godot 4.7.2 la respeta
al importar; el controlador sigue cambiando .visible). Geometría, pesos y medidas no cambian.
Uso: python receta_adan_v43_1.py ADAN_V43.glb ADAN_V43_1.glb
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

OCULTAS = ("MANO_PUNO_", "MANO_SENALAR_")


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    E = re.Editor(src)
    j = E.j
    ocultos = []
    for n in j["nodes"]:
        if n.get("name", "").startswith(OCULTAS):
            n.setdefault("extensions", {})["KHR_node_visibility"] = {"visible": False}
            ocultos.append(n["name"])
    assert len(ocultos) == 4, ocultos
    usadas = j.setdefault("extensionsUsed", [])
    if "KHR_node_visibility" not in usadas:
        usadas.append("KHR_node_visibility")
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V43.1: una sola mano visible por defecto. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return [{"operacion": "variantes de mano ocultas por defecto", "nodos": sorted(ocultos)}]


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
