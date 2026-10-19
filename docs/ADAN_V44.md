# Adán V44 · manos como la hoja del brazo (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** Martillo al rediseño de manos contra la hoja del brazo, después de V43.1 (una sola mano visible).

**Resultado:**
- `ADAN_V44.glb`, SHA-256 `4774297c039fc968095be08a4b4cdfe32acad0a55d750eec5055c79552274e05`. Reproducible: dos armados dan el mismo SHA.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v44.py ADAN_V43_1.glb ADAN_V44.glb` (unos 2 minutos).

## Medidas (`refs/personajes/adan/adan-brazo-4-vistas.jpg`, px)

| | Hoja | V43.1 | V44 |
|---|---|---|---|
| Largo de dedos | 100 % (medio 205, índice 165, anular 162, meñique 120) | 86 % | 100 % |
| Ranura entre dedos | ~4 en la base → ~16 en la punta | casi pegados (2) | 5 en la base, abanico −5°/0°/4°/9° |
| Grueso del dedo ÷ ancho | ~0.85 (lateral) | 0.92 | 0.85 |
| Pulgar abierto | ~40° | 32° | 40° |
| Grosor de palma | no más delgada que V43 | igual | igual |

**Corrección de Elio:** antes de medir propuse dedos "más delgados" y una mano "más plana". La hoja no lo pide. Lo que faltaba era largo, separación en abanico y pulgar.

## Qué cambió

1. **`copox/medicion/mano_bloques.py`:**
   - Los parámetros de estilo pasan a `ESTILO` y `ManoBloques(..., estilo=…)`.
   - Por defecto son los de V40–V43.1: las SDF de las tres poses son idénticas, así que esas versiones se siguen reproduciendo.
2. **Mano abierta:** dedos al largo de la hoja, en abanico, más delgados y con pulgar más abierto.
3. **Puño y señalar:** se rehacen con los mismos dedos y la misma pose. Sin dedos que atraviesen la palma.
4. **Línea del dorso:**
   - El tubo de la muñeca acababa 12 % más grueso que la palma y un poco más arriba. Ahora termina con la sección exacta de la palma.
   - En el mapa de quiebres la franja queda como un arco tenue (no desaparece del todo); con la luz del juego no se ve.
5. **Igual que V43.1:** costura con el antebrazo, pesos, y puño y señalar ocultos por defecto.

## Verificación

- **CHXP:** comparación V43.1 vs V44 en abierta (frente y 3/4), dorso con quiebres, puño y señalar.
- **Godot 4.7.2 con `prueba_controlador`:** caminar (abierta), correr y golpe (puño), señalar. Los dedos se distinguen a distancia de juego.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v44/`)

- `manos_v44.png`: V43.1 contra V44 en 5 tomas.
- `dorso_v43_1_v44.png`: quiebres y luz del juego.
- `godot_controlador_v44.png`

## Pendiente

- Revisión de Admin.
- Agarre de armas con los dedos nuevos. El GLB trae `AGARRE_PISTOLA`, calculado con la mano anterior, y todavía no tiene agarre de florete. El banco de pruebas no trae `PISTOLA_ALTH_PROVISIONAL.glb`, así que no se probó.
- Short al correr: queda para las pruebas de ropa.
