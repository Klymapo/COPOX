"""Cara desde video del celular: MediaPipe Face Landmarker (52 blendshapes tipo ARKit, CPU) → morphs ALTH (20 oct 2026).

Ruta AAA §6.2. Flujo: Admin graba su cara en el teléfono → el video entra a copox-modelos/entradas/ (privado) → el
workflow `alth-animacion` corre esto en Actions → sale un GLB NUEVO con el clip facial (SIN APROBAR) + curvas JSON.

  python -m copox.movimiento.cara_arkit VIDEO.mp4 --glb PERSONAJE.glb --clip Cara_Prueba --salida OUT.glb
         [--modelo face_landmarker.task] [--espejo] [--fps 30] [--neutral 1.0] [--json curvas.json]

- Calibración neutral: el primer segundo (cara relajada) se resta, para que la cara de Admin en reposo no deje al
  personaje con el ceño a medias.
- Filtro One Euro (suaviza el temblor sin retrasar los movimientos rápidos).
- MAPA_ARKIT: blendshape ARKit → [(morph ALTH, ganancia)]. FALTAN: los que la cara actual no tiene (lista para la
  cara nueva con blendshapes ARKit, que Admin aprueba y congela antes de usarlos).
- Mirada (eyeLook*): sale como curva `mirada` [x, y] para OjosALTH/LookAtModifier3D (no es morph).
Lados: ARKit/MediaPipe nombran Left/Right desde el ACTOR; los morphs _L/_R son del PERSONAJE. Video selfie espejado →
--espejo intercambia los lados.
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np

ARKIT = [
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight", "cheekPuff",
    "cheekSquintLeft", "cheekSquintRight", "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight", "eyeLookUpLeft", "eyeLookUpRight",
    "eyeSquintLeft", "eyeSquintRight", "eyeWideLeft", "eyeWideRight", "jawForward", "jawLeft", "jawOpen", "jawRight",
    "mouthClose", "mouthDimpleLeft", "mouthDimpleRight", "mouthFrownLeft", "mouthFrownRight", "mouthFunnel",
    "mouthLeft", "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight", "mouthPucker",
    "mouthRight", "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper", "mouthSmileLeft",
    "mouthSmileRight", "mouthStretchLeft", "mouthStretchRight", "mouthUpperUpLeft", "mouthUpperUpRight",
    "noseSneerLeft", "noseSneerRight", "tongueOut",
]

MAPA_ARKIT = {
    "browDownLeft": [("ceja_ceno_L", 1.0)], "browDownRight": [("ceja_ceno_R", 1.0)],
    "browInnerUp": [("ceja_triste_L", 0.7), ("ceja_triste_R", 0.7)],
    "browOuterUpLeft": [("ceja_arriba_L", 1.0)], "browOuterUpRight": [("ceja_arriba_R", 1.0)],
    "cheekPuff": [("cachete_inflar_L", 1.0), ("cachete_inflar_R", 1.0), ("boca_soplar", 0.5)],
    "cheekSquintLeft": [("cachete_subir_L", 1.0)], "cheekSquintRight": [("cachete_subir_R", 1.0)],
    "eyeBlinkLeft": [("parpado_L", 1.0)], "eyeBlinkRight": [("parpado_R", 1.0)],
    "eyeSquintLeft": [("parpado_inf_L", 0.7)], "eyeSquintRight": [("parpado_inf_R", 0.7)],
    "jawOpen": [("mandibula", 1.0), ("boca_abrir", 0.6)],
    "mouthClose": [("vis_MBP", 0.6)],
    "mouthFunnel": [("boca_o", 1.0)], "mouthPucker": [("vis_U", 1.0), ("boca_estrecha", 0.4)],
    "mouthLeft": [("boca_lado_L", 1.0)], "mouthRight": [("boca_lado_R", 1.0)],
    "mouthSmileLeft": [("comisura_arriba_L", 1.0), ("boca_sonrisa", 0.5)],
    "mouthSmileRight": [("comisura_arriba_R", 1.0), ("boca_sonrisa", 0.5)],
    "mouthFrownLeft": [("comisura_abajo_L", 1.0), ("boca_triste", 0.4)],
    "mouthFrownRight": [("comisura_abajo_R", 1.0), ("boca_triste", 0.4)],
    "mouthStretchLeft": [("boca_ancha", 0.5)], "mouthStretchRight": [("boca_ancha", 0.5)],
    "mouthPressLeft": [("boca_tensa", 0.5)], "mouthPressRight": [("boca_tensa", 0.5)],
    "mouthRollLower": [("boca_estrecha", 0.3)], "mouthRollUpper": [("boca_estrecha", 0.3)],
    "mouthLowerDownLeft": [("boca_dientes", 0.5)], "mouthLowerDownRight": [("boca_dientes", 0.5)],
}
MIRADA = {"x": (("eyeLookOutLeft", "eyeLookInRight"), ("eyeLookInLeft", "eyeLookOutRight")),
          "y": (("eyeLookUpLeft", "eyeLookUpRight"), ("eyeLookDownLeft", "eyeLookDownRight"))}
FALTAN = [k for k in ARKIT if k not in MAPA_ARKIT and not k.startswith("eyeLook")]


def _espejar(nombre):
    if "Left" in nombre:
        return nombre.replace("Left", "Right")
    if "Right" in nombre:
        return nombre.replace("Right", "Left")
    return nombre


class OneEuro:
    """Filtro One Euro (Casiez et al. 2012): suave en reposo, sin retraso en movimientos rápidos."""

    def __init__(self, fps, min_cutoff=1.5, beta=0.6, d_cutoff=1.0):
        self.fps, self.mc, self.beta, self.dc = fps, min_cutoff, beta, d_cutoff
        self.x = self.dx = None

    @staticmethod
    def _a(cutoff, fps):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau * fps)

    def __call__(self, x):
        x = np.asarray(x, float)
        if self.x is None:
            self.x, self.dx = x, np.zeros_like(x)
            return x
        dx = (x - self.x) * self.fps
        a_d = self._a(self.dc, self.fps)
        self.dx = a_d * dx + (1 - a_d) * self.dx
        cutoff = self.mc + self.beta * np.abs(self.dx)
        a = 1.0 / (1.0 + self.fps / (2 * math.pi * cutoff))
        self.x = a * x + (1 - a) * self.x
        return self.x


def curvas_a_morphs(curvas, morphs, fps, neutral_s=1.0, espejo=False, suavizar=True, ganancia=1.0):
    """curvas {arkit: array[n]} → (pesos [n, len(morphs)], mirada [n, 2], info)."""
    if espejo:
        curvas = {_espejar(k): v for k, v in curvas.items()}
    n = len(next(iter(curvas.values())))
    C = np.stack([np.asarray(curvas.get(k, np.zeros(n)), float) for k in ARKIT], 1)
    k0 = max(1, min(n, int(round(neutral_s * fps))))
    base = np.median(C[:k0], 0) if neutral_s > 0 else np.zeros(len(ARKIT))
    C = np.clip((C - base) / np.maximum(1 - base, 0.2), 0, 1) * ganancia
    if suavizar:
        f = OneEuro(fps)
        C = np.stack([f(c) for c in C])
    idx = {m: i for i, m in enumerate(morphs)}
    P = np.zeros((n, len(morphs)))
    usados, sin = set(), []
    for j, k in enumerate(ARKIT):
        for m, g in MAPA_ARKIT.get(k, []):
            if m in idx:
                P[:, idx[m]] += g * C[:, j]; usados.add(m)
            else:
                sin.append(m)
    P = np.clip(P, 0, 1)
    col = {k: C[:, j] for j, k in enumerate(ARKIT)}
    mx = 0.5 * (col["eyeLookOutLeft"] + col["eyeLookInRight"]) - 0.5 * (col["eyeLookInLeft"] + col["eyeLookOutRight"])
    my = 0.5 * (col["eyeLookUpLeft"] + col["eyeLookUpRight"]) - 0.5 * (col["eyeLookDownLeft"] + col["eyeLookDownRight"])
    info = {"cuadros": n, "fps": fps, "morphs_usados": sorted(usados), "faltan_en_cara": FALTAN,
            "morphs_mapeados_inexistentes": sorted(set(sin))}
    return P, np.stack([mx, my], 1), info


def video_a_curvas(video, modelo, fps_salida=30):
    """MediaPipe Face Landmarker (modo VIDEO) → {arkit: array}. Requiere `mediapipe` y `opencv-python-headless`."""
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    op = vision.FaceLandmarkerOptions(base_options=mpp.BaseOptions(model_asset_path=modelo),
                                      running_mode=vision.RunningMode.VIDEO, output_face_blendshapes=True, num_faces=1)
    cap = cv2.VideoCapture(video)
    fps_v = cap.get(cv2.CAP_PROP_FPS) or 30.0
    paso = max(1, int(round(fps_v / fps_salida)))
    filas, i, ultimo = [], 0, None
    with vision.FaceLandmarker.create_from_options(op) as lm:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if i % paso == 0:
                img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
                r = lm.detect_for_video(img, int(i * 1000 / fps_v))
                if r.face_blendshapes:
                    ultimo = {c.category_name: c.score for c in r.face_blendshapes[0]}
                filas.append(ultimo or {})
            i += 1
    cap.release()
    return {k: np.array([f.get(k, 0.0) for f in filas]) for k in ARKIT}, fps_v / paso


def main(argv=None):
    ap = argparse.ArgumentParser(description="Video de cara → clip facial ALTH (MediaPipe, CPU)")
    ap.add_argument("video")
    ap.add_argument("--glb", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--salida", required=True, help="GLB NUEVO con el clip")
    ap.add_argument("--modelo", default="face_landmarker.task")
    ap.add_argument("--espejo", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--neutral", type=float, default=1.0)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    from copox.medicion.rostro_edicion import Editor
    from copox.movimiento import clip_gltf as cg
    curvas, fps = video_a_curvas(a.video, a.modelo, a.fps)
    E = Editor(a.glb)
    morphs = cg.nombres_morphs(E)
    P, mirada, info = curvas_a_morphs(curvas, morphs, fps, a.neutral, a.espejo)
    t = np.arange(len(P)) / fps
    cg.agregar_clip_morphs(E, a.clip, t, P)
    E.log.append({"operacion": "clip facial desde video (MediaPipe)", "clip": a.clip, **info})
    E.guardar(a.salida, nota=f"Clip facial {a.clip} desde video. SIN APROBAR.")
    if a.json:
        json.dump({"fps": fps, "morphs": morphs, "pesos": np.round(P, 4).tolist(), "mirada": np.round(mirada, 4).tolist(),
                   "info": info}, open(a.json, "w"))
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
