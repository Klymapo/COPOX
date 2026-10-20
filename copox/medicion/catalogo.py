"""Catálogo ALTH (19 oct 2026): lo que ya funcionó con Theo, como piezas reutilizables por ficha de personaje.

- ROPA: conjuntos de prendas (receta + parámetros por defecto). Los parámetros de la ficha se MEZCLAN encima.
- PELO / CALZADO: qué nodos de la base congelada quedan visibles (KHR_node_visibility).
Para agregar una prenda o un peinado nuevo: research brief (skill investigar-referencias) → receta → entrada aquí.
"""
from __future__ import annotations

ROPA = {
    "ninguna": None,
    # Theo: camisa + chaleco + pantalón + corbata, técnica del short (ropa_tubos). Receta: docs/medicion/vestir_theo_v3.py
    "traje_chaleco": {
        "receta": "vestir_theo_v3",
        "grupos": {                                   # grupo de la ficha → (módulo, variable)
            "camisa": ("v3", "CAM"), "chaleco": ("v3", "CHA"), "pantalon": ("v3", "PAN"), "corbata": ("v3", "CORB"),
            "corbata_forma": ("v2", "CORBATA"), "chaleco_region": ("v2", "CHALECO"), "camisa_region": ("v2", "CAMISA"),
            "tris": ("v3", "TRIS"),
        },
        "colores": ("v2", "COL"), "telas": ("v2", "TELA"), "visible": ("v2", "VISIBLE"),
    },
    # Alastor (originales): camisa de manga larga + corbata + pantalón (traje_chaleco SIN chaleco) + abrigo largo abierto
    # con solapas + cinturón con hebilla + gafas de pasta. Receta: docs/medicion/alastor.py. Briefs: abrigo, gafas.
    "abrigo_detective": {
        "receta": "alastor",
        "modulos": {"al": "alastor", "v3": "vestir_theo_v3", "v2": "vestir_theo_capas"},
        "grupos": {
            "camisa": ("v3", "CAM"), "pantalon": ("v3", "PAN"), "corbata": ("v3", "CORB"),
            "corbata_forma": ("v2", "CORBATA"), "camisa_region": ("v2", "CAMISA"), "tris": ("v3", "TRIS"),
            "abrigo": ("al", "ABRIGO"), "cinturon": ("al", "CINTURON"), "gafas": ("al", "GAFAS"), "pelo": ("al", "PELO"),
        },
        "colores": [("v2", "COL"), ("al", "COL")], "telas": [("v2", "TELA"), ("al", "TELA")], "visible": ("v2", "VISIBLE"),
    },
}

PELO = {
    "theo": {"CAPA_PELO_THEO": True, "CAPA_PELO_CORTO": False, "CAPA_PELO_MECHONES": False, "CAPA_GUIA_CAPILAR": False},
    "corto": {"CAPA_PELO_THEO": False, "CAPA_PELO_CORTO": True, "CAPA_PELO_MECHONES": False, "CAPA_GUIA_CAPILAR": False},
    "mechones": {"CAPA_PELO_THEO": False, "CAPA_PELO_CORTO": False, "CAPA_PELO_MECHONES": True, "CAPA_GUIA_CAPILAR": False},
    "alastor": {"CAPA_PELO_THEO": False, "CAPA_PELO_CORTO": True, "CAPA_PELO_MECHONES": False, "CAPA_GUIA_CAPILAR": False,
                "CAPA_PELO_ALASTOR": True},     # el casquete corto (recoloreado) rellena el cráneo bajo las masas     # lo construye la receta alastor (pelo de los originales)
    "rapado": {"CAPA_PELO_THEO": False, "CAPA_PELO_CORTO": False, "CAPA_PELO_MECHONES": False, "CAPA_GUIA_CAPILAR": False},
}

CALZADO = {
    "zapato": {"PIES_ZAPATO": True, "PIES_TENIS": False, "PIES_DESCALZOS": False},
    "tenis": {"PIES_ZAPATO": False, "PIES_TENIS": True, "PIES_DESCALZOS": False},
    "descalzo": {"PIES_ZAPATO": False, "PIES_TENIS": False, "PIES_DESCALZOS": True},
}

MANOS = {
    "abierta": {"MANO_ABIERTA_L": True, "MANO_ABIERTA_R": True, "MANO_PUNO_L": False, "MANO_PUNO_R": False,
                "MANO_SENALAR_L": False, "MANO_SENALAR_R": False},
}
