"""Adán V46.1 (sobre V45): pendientes de V46 en el pie.

Pedido de Admin (19 oct 2026): "Continúa los pendientes de V46". Pendientes de docs/ADAN_V46.md:
1. Abultamiento de lado: el pie llegaba a lo más ancho a media altura (11.4 cm) y se volvía a cerrar a la planta
   (10.4 cm), porque el ensanche del talón también se aplicaba a las esquinas de adelante. Ahora sólo se abre el talón
   (vista BACK de la hoja); los lados de adelante son planos que bajan de la pierna y se abren hacia los dedos.
2. Escalón alrededor del tobillo: el paso de la sección de la pierna a la del pie era muy corto (15 % de la altura del
   pie). Ahora es del 35 %.
3. Dedos más largos y delgados, como la hoja: más bajos, más separados, más caídos y con las puntas más escalonadas.
4. Planos un poco más marcados: esquinas de las secciones de 4–2.5 mm (V46: 5.5–3.5 mm), con sombreado suave.
El resto es V46: pierna de V42–V45, pliegue del tobillo a 0.82 del fondo de la pierna, talón que sigue la pierna.
Uso: python receta_adan_v46_1.py ADAN_V45.glb ADAN_V46_1.glb
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import receta_adan_v46 as v46  # noqa: E402

PIE_461 = {**v46.PIE, "abre_frente": 0.0, "transicion": 0.35, "radio": (0.004, 0.0025),
           "alto_dedos": 0.017, "alto_gordo": 1.2, "largo_dedos": 0.044, "hueco": 0.0045, "caida": 0.45,
           "escalon": 0.010}


def main(src, dst):
    from copox.medicion import rostro_edicion as re
    from copox.medicion.compactar import compactar
    p0 = dict(v46.PIE)
    v46.PIE.clear(); v46.PIE.update(PIE_461)
    try:
        E = re.Editor(src)
        log = [v46.piernas(E)]
    finally:
        v46.PIE.clear(); v46.PIE.update(p0)
    tmp = dst + ".tmp.glb"
    E.guardar(tmp, nota="Adán V46.1: pendientes del pie de V46. SIN APROBAR.")
    compactar(tmp, dst)
    os.remove(tmp)
    return log


if __name__ == "__main__":
    for x in main(sys.argv[1], sys.argv[2]):
        print(x)
