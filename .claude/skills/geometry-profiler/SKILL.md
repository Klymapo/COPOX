---
name: geometry-profiler
description: Perfilado determinista y escalabilidad del motor geométrico COPOX en loops y mallas, sin introducir dependencias ni prometer aceleraciones no medidas.
---

# COPOX · Geometry Profiler

## Objetivo
Medir coste computacional real **después** de validar identidad de las referencias, contornos, UV/skin y topología. La optimización no sustituye los gates artísticos.

## Instrumentación
- `python -m tools.maniqui.g2c_benchmark` mide iteraciones 12/19, 128/257 y 512/769 en el mismo runner; reporta duración, versiones y hash determinista de triángulos a `docs/maniqui/g2c/BENCHMARK_SYNTHETIC.json`.
- No asignar una ganancia Numba de 10–100x sin baseline medido y aceleración sobre un loop efectivamente crítico.
- Distinguir complejidad: `distance.cdist` es NxM en tiempo y memoria; `cKDTree` evita matriz densa pero NO certifica winding/correspondencia de dos loops.
- Usar perfiles en una máquina reproducible para `extract loops`, `find pair`, `advancing front`, `geometry gates`, `export GLB`, `Godot import` y renders. Identificar el gasto real antes de compilar.
- Evaluar Numba sólo en camino caliente con tests idénticos, comparativa byte/triángulo, precisión numérica y fallback Python/NumPy gratuito.
- No dividir artificialmente una costura topológica indivisible para paralelizarla. Paralelizar cassettes o modelos **independientes**, con SHA y autorización por modelo.
- Fijar versiones de Python/NumPy/SciPy/Pillow en el workflow reproducible y documentar CPU/tiempos.
- Todo candidato de optimización debe generar los mismos triángulos o justificar desviaciones con mejora comprobada en **todas las referencias**, no sólo menor latencia.

## Fallos que impiden promoción
Sin contorno facial validado, con material/UV/skin no soportado, autointersección no auditada, o importación Godot pendiente → `RESEARCH_REQUIRED`. Optimización nunca equivale a aprobación.
