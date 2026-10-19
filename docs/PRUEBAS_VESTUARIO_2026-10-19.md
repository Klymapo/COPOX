# Pruebas de ropa ajustada y pelo por mechones sobre Adán V48.3 (19 oct 2026)

Pedido de Admin: "Hagamos unas pruebas" → ropa ajustada en movimiento + pelo por mechones, con capturas y GIF.
Skill usada: `alth-meta-vestuario-cabello` (Drive/SKILLS). Ninguna prueba cambia el GLB de Adán: son archivos aparte.

## Ropa ajustada (`docs/medicion/prueba_ropa_adan.py`, `copox/medicion/ropa_ajustada.py`)
- Camisa `medidos/camisa_blanca #FBEFE1`, pantalón `medidos/pantalon_azul #4A5770` (paleta).
- Técnica: cada parte es el cuerpo inflado 4–4.5 mm (sólido, marching cubes), recortado por planos; partes separadas
  como las piezas del cuerpo (torso de camisa, dos mangas, cadera del pantalón, dos perneras) para no pellizcar hombro ni
  ingle al posar. Puños y vuelta del pantalón: anillo +3 mm.
- Pesos: los de la piel visible exacta debajo (interpolación baricéntrica, muestras a 2 mm).
- En la prueba (derivado reversible) se ocultan los triángulos de piel tapados por la ropa y el short.
- Errores corregidos en el camino: planos locales lejanos con signo al azar (piezas abiertas), banda con huecos entre
  vértices espaciados (hacía cráteres), superficies fantasma internas, tela delgada que el simplificador abría.
- Pendiente visto: la cadera del pantalón (hecha sobre el short) marca un escalón sobre las perneras.

## Pelo por mechones (`docs/medicion/prueba_pelo_mechones.py`, `copox/medicion/pelo_mechones.py`)
- 16 mechones (copete que barre a su izquierda, lados, nuca y coronilla) como cadenas de elipsoides sobre la cáscara de
  V48.3. Raíz ancha, punta suave. Sin huesos secundarios: el pelo sigue a la cabeza rígido.

## Decisiones abiertas
- Short y pies intercambiables (Admin, 19 oct): hoy el cuerpo no tiene cadera ni entrepierna (el short tapa el hueco).
  Para quitar el short hace falta una pieza de pelvis en el cuerpo. Propuesta aparte.
