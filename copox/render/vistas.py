"""Vistas con nombre y códigos de vista compartidos (Elio ↔ Argos).

Un código de vista es texto plano ``clave=valor`` separado por ``;``. Puede
empezar con el nombre de una vista guardada y cambiar solo lo necesario:

    frente
    frente;modo=arcilla;tam=1024
    cara_34;clip=TalkGestureFace-loop;t=0.5;ocultar=CAPA_GUIA_CAPILAR
    yaw=20;elev=10;dist=2.5;region=cara;enc=auto;modo=curvatura

Claves:
  yaw, elev, roll   grados (yaw 0 = frente, 90 = costado izquierdo del personaje, 180 = espalda)
  dist              'orto' (ortográfica) o distancia en unidades del modelo (perspectiva)
  region            cuerpo | cara | mano_izq | mano_der | pies (qué se encuadra con enc=auto)
  enc               'auto' o 'alto,cx,cy': alto visible y centro en unidades del modelo
                    (fijo: misma toma para todas las versiones de un modelo)
  clip, t           animación y fracción 0–1 ('reposo' = sin animación)
  modo              color | arcilla | malla | normales | curvatura | clases | clases_tri
  tam               lado de la imagen en px (512 iterar, 1024 final)
  sombreado         suave | facetas | archivo (normales guardadas en el GLB, como Godot)
  ocultar           nombres de nodo o de material separados por coma
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

MODOS = ("color", "arcilla", "malla", "normales", "curvatura", "clases", "clases_tri")


@dataclass
class Vista:
    nombre: str = "libre"
    yaw: float = 0.0
    elev: float = 5.0
    roll: float = 0.0
    dist: float | None = None
    region: str = "cuerpo"
    enc: str = "auto"
    clip: str = "Idle-loop"
    t: float = 0.0
    modo: str = "color"
    tam: int = 512
    sombreado: str = "suave"
    ocultar: tuple = field(default_factory=tuple)

    def codigo(self) -> str:
        d = "orto" if self.dist is None else f"{self.dist:g}"
        s = (f"yaw={self.yaw:g};elev={self.elev:g};roll={self.roll:g};dist={d};region={self.region};"
             f"enc={self.enc};clip={self.clip};t={self.t:g};modo={self.modo};tam={self.tam};sombreado={self.sombreado}")
        if self.ocultar:
            s += ";ocultar=" + ",".join(self.ocultar)
        return s


# Encuadres fijos medidos sobre Adán/Theo (alto total ≈ 0.85 u; línea de ojos ≈ 0.65 u)
_CUERPO = "1.0,0,0.43"
_CARA = "0.5,0,0.65"

GUARDADAS = {
    "frente": Vista("frente", 0, 5, enc=_CUERPO),
    "tres_cuartos": Vista("tres_cuartos", 35, 8, enc=_CUERPO),
    "perfil_izq": Vista("perfil_izq", 90, 5, enc=_CUERPO),
    "perfil_der": Vista("perfil_der", -90, 5, enc=_CUERPO),
    "espalda": Vista("espalda", 180, 5, enc=_CUERPO),
    "tres_cuartos_espalda": Vista("tres_cuartos_espalda", 145, 8, enc=_CUERPO),
    "cara_frente": Vista("cara_frente", 0, 0, region="cara", enc=_CARA),
    "cara_34": Vista("cara_34", 35, 0, region="cara", enc=_CARA),
    "cara_perfil": Vista("cara_perfil", 90, 0, region="cara", enc=_CARA),
    "cara_espalda": Vista("cara_espalda", 180, 0, region="cara", enc=_CARA),
    "mano_izq": Vista("mano_izq", 60, 5, region="mano_izq"),
    "mano_der": Vista("mano_der", -60, 5, region="mano_der"),
    "pies": Vista("pies", 0, 20, region="pies"),
}

HOJA = ("frente", "tres_cuartos", "perfil_izq", "espalda")


def leer(codigo: str) -> Vista:
    partes = [p.strip() for p in codigo.split(";") if p.strip()]
    v = Vista()
    if partes and "=" not in partes[0]:
        nombre = partes.pop(0)
        if nombre not in GUARDADAS:
            raise KeyError(f"Vista desconocida: {nombre}. Guardadas: {', '.join(GUARDADAS)}")
        v = replace(GUARDADAS[nombre])
    for p in partes:
        k, _, x = p.partition("=")
        k, x = k.strip(), x.strip()
        if k in ("yaw", "elev", "roll", "t"):
            setattr(v, k, float(x))
        elif k == "dist":
            v.dist = None if x == "orto" else float(x)
        elif k == "tam":
            v.tam = int(x)
        elif k == "modo":
            if x not in MODOS:
                raise ValueError(f"Modo desconocido: {x}. Modos: {', '.join(MODOS)}")
            v.modo = x
        elif k == "ocultar":
            v.ocultar = tuple(n for n in x.split(",") if n)
        elif k in ("region", "enc", "clip", "sombreado", "nombre"):
            setattr(v, k, x)
        else:
            raise KeyError(f"Clave desconocida: {k}")
    return v
