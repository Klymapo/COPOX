# Adán V42 · piernas y pies de bloques (SIN APROBAR)

**Pedido de Admin (18 oct 2026):** "Sigue con piernas desde cadera y pies".

**Resultado:**
- `ADAN_V42.glb`; el SHA-256 está en `copox-modelos/adan/SHA256SUMS` (`84faed12…65fa`).
- Reproducible bit a bit: dos armados en paralelo dan el mismo SHA.
- V41 exacto se reproduce con el commit `2c2b968`: V42 cambia código compartido con V40 y V41.
- Receta: `GODOT_BIN=… docs/medicion/receta_adan_v42.py ADAN_V22_HABLA.glb ADAN_V42.glb` (V41 + este paso).

## Medidas

La regla es el dobladillo del short, porque en V41 ya coincide con la hoja.
- **Ancho de la pierna:** 0.35 del ancho del short en el dobladillo, igual en la hoja del cuerpo y en V41. No cambia.
- **Pliegue del tobillo:** al 44 % de la altura del dobladillo (hoja del cuerpo, de frente): y = 0.059.
- **Largo del pie:** 1.8 veces el fondo de la pierna (hoja de pies, de lado): 0.18. V41 ya medía eso.

En medidas, piernas y pies ya coincidían. Lo que no coincidía era la forma: el pie era una "bota" redonda con suela y sin dedos.

## Qué cambió (`copox/medicion/pie_geo.py`)

Una superficie implícita por pierna reemplaza `Pierna*_PIEL`, `Pie*`, `Cana*` y `Suela*`:
- **Pierna:** un prisma recto que sale de dentro del short y se angosta un poco hacia el tobillo.
- **Pie:** sale de la pierna con planos inclinados, como en la hoja de pies:
  - El lado de adentro es recto.
  - Afuera y atrás (talón) se abren hacia el piso.
  - El empeine es plano bajo la pierna y baja en rampa recta hasta los dedos.
- **Dedos:** cuatro bloques separados; el gordo, hacia adentro, es más ancho y más largo.
- **Tobillo:** arista suave (unión 0.005).
- **Planta:** al piso exacto (y = 0).
- **Pierna hasta la cadera.**
  - Sube dentro del short hasta 1 cm bajo la cadera, para que al caminar nunca se vea su tapa.
  - Dentro del short es 22 % más angosta: al correr no atraviesa la tela.
  - Sobre la rodilla pesa en el muslo (85 % UpperLeg), con una rampa de 2 cm en la rodilla.
- **Pesos:** transferidos de las piezas viejas (pierna, pie, caña y suela), con Toes en los dedos.

## Correcciones de la revisión independiente (primera prueba de V42)

1. **Dobladillo con picos:** las bocas del short ahora se cortan por planos exactos (`short_geo.recortar`). La altura del dobladillo no cambia.
2. **Muesca trasera como ranura:** ahora es una V recta (medio ancho 24 mm en el dobladillo).
3. **Solapa y huecos del short al caminar (Godot):**
   - Pesos explícitos: Hips arriba. Bajo la entrepierna, cada lado sigue a su muslo hasta 92 %, y menos cerca del centro.
   - La tela es de dos caras: por la muesca y las perneras se ve el interior, no un hueco.
4. **Talón:** se abre también hacia adentro, pero sólo atrás. El tobillo es una arista suave (unión 0.005), sin anillo.
5. **Muñeca como puño de manga:** la palma ahora es una cuña, gruesa en la muñeca (×1.75) y delgada en los nudillos, como en la hoja del brazo. La mano conserva el perfil del anillo del antebrazo en 28 mm.

## Segunda revisión independiente

- **Dobladillo y muesca:** PASS. Queda una duda: atrás la muesca se lee delgada.
- **Pie:** PASS. Talón abierto a los dos lados y cuatro dedos. Queda una duda por un pliegue leve en el tobillo.
- **Short al caminar y correr en Godot:** FAIL para el revisor.
  - Al caminar, la tela se arruga donde la jala el muslo.
  - Al correr, el frente se levanta.
  - Ya no hay huecos ni piernas que atraviesen la tela. Lo que queda es cómo la tela sigue al muslo, y eso se decide visualmente; lo decide Admin.
- **Muñeca:** FAIL para el revisor. Queda una línea en el dorso, donde empieza la cuña de la palma. Ya no es el escalón de V40.
- Se publica SIN APROBAR para que Admin decida. Siguiente técnica posible para la tela: una forma correctiva o un hueso de tela en la entrepierna.

## Pendiente

- La costura trasera del short y el pliegue del frente.
- La mano con pistola, después de aprobar las manos.

## Evidencia (rama `capturas`, `capturas/2026-10-18/adan_v42/`)

- `hoja_v42.png`: la referencia del cuerpo arriba y V42 abajo.
- `pies_v42.png`: los pies de cerca, contra la hoja de pies.
- `short_v42.png`: el short en 4 vistas.
- `manos_v42.png`: mano abierta (3/4 y por la espalda), puño y señalar.
- `godot_v42.png`: Idle, dos cuadros de Walk, Run y PointFwd.
