---
name: scene-director
description: Crea y valida escenas 3D de Godot, iluminación, cámaras, composición, props, navegación y eventos, contrastando cada vista y referencia de encuadre aportada.
---

# Scene Director · dirección de escenas y cámaras

1. Inventariar **todas** las referencias visuales del escenario: plano, vistas, distribución, escala, iluminación, materiales, personajes, poses y secuencias. Asociar cada imagen/video a la cámara, altura, focal y estado de la escena conocido; marcar desconocidos.
2. Leer briefs narrativos y las reglas técnicas del repo. Para AlasTheo: no editar `GameState` ni autoloads sin permiso, no asserts/casts prohibidos ni nuevos autoloads. Sólo API pública y tests establecidos.
3. Definir coordenadas, unidades, suelo, colisionadores, navegación, escala de puertas y props, iluminación, materiales y prioridades visuales. Construir escenas deterministas a partir de assets con procedencia comprobada.
4. Establecer cámaras reproducibles con posición, orientación, FOV/ortográfica, distancia y aspect ratio. En escenas isométricas verificar oclusión, lectura del gameplay, dirección de luz y proporciones del personaje.
5. Para cada referencia proporcionada, reproducir su encuadre o marcar expresamente que la cámara no es equivalente. Comparar con `visual-critic` TODAS las vistas e instantes, sin elegir una imagen favorecida.
6. Validar iluminación y sombras, objetos flotantes, z-fighting, materiales, escala y contacto con suelo; para cortes narrativos comprobar continuidad de acciones, dirección de mirada y montaje.
7. Godot headless: pruebas de escena y evidencias reales, luego reproducción interactiva si es posible. No inventar fps ni estabilidad sin medir.
8. Entregar escenas/recursos en rama experimental, capturas multivista, evidencia con cámaras/semillas/fotogramas, reporte técnico y revisión Admin antes de fusionar.

