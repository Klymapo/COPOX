"""Cine ALTH (20 oct 2026): cinemáticas renderizadas con Blender Cycles en CPU, repartidas en GitHub Actions.

Ruta: docs/RUTA_AAA.md §5 y §6.3. Decisión de Admin (20 oct): render final en Blender, todo en la nube (Actions).
Piezas:
  escena.py          esquema de la escena (JSON) + validación + reparto de cuadros (sin bpy)
  render_blender.py  corre DENTRO de Blender (alth-python): importa el GLB, respeta KHR_node_visibility, aplica el
                     clip, cámara por cuadros clave, luz de estudio ALTH, Cycles CPU → PNG por cuadro
  hornear_ao.py      corre dentro de Blender: hornea oclusión ambiental por vértice → .npz (posición, ao)
  aplicar_ao.py      numpy: lleva el .npz al COLOR_0 de un GLB nuevo (no toca el original)
  ensamblar.py       cuadros → MP4 (ffmpeg)
"""
