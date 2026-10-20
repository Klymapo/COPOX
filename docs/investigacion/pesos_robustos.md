# Brief · Transferencia robusta de pesos

Fecha: 2026-10-20 · Brief válido: sí · Skill: investigar-referencias · Herramienta hecha (Admin: «termina las herramientas», sin pruebas piloto).

## Alcance
Todas las prendas nuevas. Implementación: `copox/medicion/pesos_robustos.py` (licencia del método de referencia: MIT, verificada).

## Fuentes
- **Abdrashitov et al., *Robust Skin Weights Transfer via Weight Inpainting*,** SIGGRAPH Asia 2023 Technical Communications. Copia los pesos solo donde la correspondencia cuerpo → prenda es confiable (distancia y ángulo de normal) y **rellena** el resto resolviendo un problema de suavidad (Laplaciano).
  - Proyecto: https://dgp.toronto.edu/~rinat/projects/RobustSkinWeightsTransfer/index.html
  - **Código: licencia MIT** (https://github.com/rin-23/RobustSkinWeightsTransferCode). Python con libigl. La implementación es independiente de Blender.
- **80.lv:** un add-on de Blender de un clic basado en el método (https://80.lv/articles/grab-this-one-click-blender-tool-for-effortless-weight-transfers/). Es de terceros, así que no lo uso: se implementa el método directo.

## Aplicación
- Reemplaza el «peso por piel más cercana» en todas las prendas.
- Resuelve en su origen los picos (abrigo V04–V06) y el PLATEAU de capas que se atraviesan (Theo).
- **Implementación:**
  - El paso 1 (correspondencia confiable) se hace en numpy.
  - El paso 2 (inpainting) es un sistema lineal disperso con `scipy.sparse`. Hay que verificar que esté instalado; no necesita libigl si armamos el Laplaciano cotangente nosotros.
- **Regresión:** CHXP con todos los clips de locomoción y de sentarse, no solo 3 GIF.

## Riesgos
- Prendas muy holgadas (el faldón del abrigo) tienen poca correspondencia confiable. El inpainting lo cubre, pero puede quedar «rígido»: se combina con resortes en el faldón.
- Hay que soldar los duplicados antes (lección de V09).
