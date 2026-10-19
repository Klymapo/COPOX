"""COPOX · renderizador para Elio y Argos (NumPy + Pillow). Ver docs/COPOX_RENDER.md y LEEME_IA.md."""
from .sesion import Sesion, Resultado
from .vistas import Vista, GUARDADAS, leer

__all__ = ["Sesion", "Resultado", "Vista", "GUARDADAS", "leer"]
