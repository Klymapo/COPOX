# Brief · Ropa por capas con textura (camisa, chaleco, corbata, pantalón)

Fecha: 2026-10-19 · Brief válido: sí · Skill: investigar-referencias

## Fuentes
- He Spoke Style, *Dress shirt parts* (https://hespokestyle.com/dress-shirt-parts-terminology/) y Sew Guide, *Parts of a
  shirt* (https://sewguide.com/parts-of-a-shirt/): cuello (puntas, pie), tapeta de botones, canesú, puño, dobladillo.
- Permanent Style, *Guide to cloth weaves* (https://www.permanentstyle.com/2016/09/the-guide-to-cloth-weaves-and-designs)
  y NPS, *Weaving patterns* (https://www.nps.gov/articles/000/weaving-patterns.htm): tafetán (camisa de algodón),
  sarga diagonal (pantalón de lana), satén/brillo (seda de corbata).
- Unreal forums, *Layered clothing* (https://forums.unrealengine.com/t/layered-clothing/321609): prendas como mallas
  separadas sobre el mismo esqueleto, encendidas/apagadas por visibilidad.
- Hoja de Theo: manga larga arremangada, chaleco negro con V y botones, corbata azul, pantalón recto con vuelta.

## Marcas visibles
- Camisa: cuello con dos puntas sobre el chaleco, tapeta (solo en la V), puño/vuelta de manga, pliegues en codo.
- Chaleco: dos paneles delanteros que se cruzan en V con orilla gruesa, 4 botones, puntas abajo, sisa con orilla,
  espalda lisa.
- Corbata: nudo con volumen en el cuello; hoja que cuelga despegada del pecho.
- Pantalón: pretina, raya delantera, caída recta, vuelta (dobladillo) como banda; termina sobre el empeine.

## Medidas (real → ALTH)
- Holgura "un poco": torso 3–4 mm sobre la piel (u ALTH), 2–3 mm entre capas; pierna recta (más holgura abajo).
- Grosor de tela visible en orillas: 1.5–2.5 mm; vuelta del pantalón 14–18 mm de alto.

## Simplificación ALTH
- Cada prenda es su propia malla con grosor y orillas biseladas; la tela pasa por encima de los huecos del cuerpo
  (cierre morfológico: no se pega a cada concavidad). Detalles (botones, nudo, vuelta) como piezas simples.
- Textura pequeña por tela (generada aquí, licencia propia): tafetán, sarga, tejido cerrado, satén, cuero; color base de
  la paleta, la textura solo modula ±8 %. Coordenadas UV por proyección triplanar/caja.

## Técnica
- `copox/medicion/ropa_capas.py`: Prenda = campo del cuerpo (o de la capa de abajo) + holgura, con cierre
  (dilatar→erosionar) para que cuelgue; cáscara con grosor; orillas por plano/región; piezas extra (cuello, botones,
  nudo, vuelta). Cada prenda en su nodo (KHR_node_visibility) con pesos de la piel visible.
- `copox/medicion/texturas_tela.py`: texturas tileables 128–256 px por tela (NumPy), embebidas en el GLB.

## Revisiones CHXP
- Capas: en Idle/Walk/Run/Jump/Sit, la capa de arriba no queda dentro de la de abajo (penetración ≤ 1 mm en ≥ 99 %).
- Límite pantalón–zapato: sin piel visible entre dobladillo y zapato; dobladillo no atraviesa el zapato.
- Paleta por color promedio de la textura (ΔE ≤ 6); triángulos ≤ tope; SENKU cuerpo ≥ Theo vestido v1.

## Plan de prueba
- `docs/medicion/vestir_theo.py` v2 sobre Adán V50; CHXP V3 + GIF Walk/Run/Jump. Máx. 3 iteraciones por prenda.

## Riesgos / dudas
- Texturas pequeñas pueden "ensuciar" el facetado plano: modulación baja (±8 %).
