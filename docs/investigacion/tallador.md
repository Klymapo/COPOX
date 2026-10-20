# Brief · Tallador de prendas y mechones con bisel

Fecha: 2026-10-20 · Brief válido: sí · Skill: investigar-referencias · Herramienta hecha (Admin: «termina las herramientas», sin pruebas piloto).

## Alcance
Primera prenda prevista: pantalón de Theo (cuando Admin dé «Martillo»). Implementación: `copox/medicion/tallador.py`.

## Fuentes
- **80.lv, *001agt stylized character art workflow*.** El flujo del gremio va de bloque a esculpido, retopo, UV, horneado y textura. El bisel se controla con *creasing*: la distancia entre el nivel de subdivisión y el de pliegue define qué tan suave es la arista. «Primero las formas grandes; el detalle no arregla formas malas.» (https://80.lv/articles/001agt-stylized-character-art-workflow-from-blockout-to-render)
- **Gnomon / K. Tunsworth, *Modelling a Stylised Character for Games*.** Mismo flujo, en low poly. (https://katunsworth.artstation.com/projects/29lzOg)
- **Proyecto:**
  - Las piezas que más se parecen a la referencia son las **no** implícitas: el pie y el zapato con loft por secciones (V46) y el rizo con barrido superelíptico (Alastor V06+).
  - Lección «Más de 20 rondas G2 en PLATEAU»: generar la pieza en lugar de parcharla.
- **Referencia de Theo:** `refs/personajes/joven-rubio-4-vistas.jpg` y la lámina T-pose del 20 oct.

## Marcas visibles del pantalón (referencia de Theo)
- **Pierna:** ancha arriba, se angosta un poco hacia el tobillo. La sección es casi rectangular con esquinas redondeadas, no un tubo.
- **Raya frontal y trasera:** una arista vertical marcada al centro de cada pierna (se ve como cambio de tono).
- **Dobladillo:** una vuelta gruesa (≈ 1/6 del largo visible de la pierna), un poco más ancha que la pierna, con arista superior marcada.
- **Pretina:** banda limpia y recta (hoy es dentada). La entrepierna es una V limpia.
- **Color:** azul medio. Ya está en la paleta del conjunto `traje_chaleco`.

## Técnica propuesta
1. **Secciones poligonales** a lo largo de cada pierna (unas 10 alturas). Cada una es un rectángulo superelíptico de **12 lados**: ancho, fondo y radio de esquina salen de SENKU y de la piel de Adán más la holgura.
2. **Puente entre secciones** (quads), sin SDF, sin marching cubes y sin simplificar. Low-poly por construcción, aprox. 600–900 tris por pierna.
3. **Aristas duras marcadas:**
   - raya delantera y trasera (un vértice de la sección marcado como pico);
   - borde de la pretina;
   - borde superior e inferior del dobladillo.
4. **Bisel analítico:** cada arista dura se reemplaza por 2–3 segmentos con radio paramétrico. Se hace en numpy sobre la sección, como el rizo, así que **no depende de bpy**.
5. **Normales ponderadas por área** y partidas en las aristas duras. Se duplican vértices solo en la costura dura y el bisel queda suave. Calculado en numpy.
6. **Dobladillo:** anillo extra hacia afuera (+3 mm), con su propia sección y bisel.
7. **Pretina y entrepierna:** las secciones de ambas piernas se unen en una pelvis de secciones (técnica de pelvis V2: torso extruido más muslos que se unen en la V).
8. **UV:** por sección. U = perímetro normalizado y V = largo acumulado. La costura va en la cara interna de la pierna. Sale gratis.
9. **Pesos:** copia desde la piel de Adán (con soldado y alisado como en V11) y, después, transferencia robusta (sección B).

## Por qué numpy y no Blender (`bmesh.ops.bevel`)
- Hoy `pip` no llega a PyPI desde la sesión: el proxy rechaza `pypi.org`, así que `alth-python` no se puede instalar aquí.
- Todo el pipeline actual ya es numpy + Godot.
- El bisel y las normales ponderadas sobre secciones ordenadas son sencillos de hacer en numpy, y mantienen las recetas reproducibles bit a bit.
- **Blender queda para:** el horneado de oclusión y curvatura (Cycles) y el render de cine. Se correrá en GitHub Actions, donde PyPI sí está disponible, o en esta sesión cuando el dominio esté permitido.

## Medidas (con SENKU)
- Por medir en la hoja de 4 vistas: ancho de la pierna arriba y abajo, alto del dobladillo, ancho del dobladillo y altura de la pretina.
- Todo relativo a la unidad ED y a la piel de Adán.

## Revisiones CHXP
- `capas_visibles`, `senku_regiones`, `normales`, `sin_flotantes`, `pesos_normalizados` y `triangulos_tope`.
- **Nueva (propuesta CHXP V4):** `nitidez_aristas`, histograma de normales contra la referencia por región.
- **Lámina T-pose contra referencia y primer plano** del bajo y de la pretina.

## Criterio de éxito (3 intentos máximo)
- El revisor visual reconoce el pantalón de la referencia: raya, dobladillo, sección rectangular y pretina limpia.
- Sin atravesar en Walk, Run ni Sit.
- Si no llega en 3 intentos: **PLATEAU** y se vuelve a la baseline V4_2.
