# Importar el modelo en Godot 4

1. Extrae el paquete y copia `model_godot.glb` en `res://assets/characters/` de tu proyecto.
2. Espera a que Godot termine la importación. Arrastra el GLB a una escena 3D.
3. Mantén la escala del nodo en `(1, 1, 1)` y comprueba su altura y apoyo en el suelo.
4. Revisa de frente, perfil y espalda: silueta, transparencias, texturas y orientación. Ajusta el giro horizontal en Stylizer si hace falta y exporta otra versión.
5. Consulta `report.json`. Los avisos son puntos para revisar, no una puntuación de parecido.
6. Para editar, abre `model_prepared.blend` en Blender. Guarda tus correcciones y vuelve a exportar como GLB.

## Qué hace la preparación

- Normaliza altura en metros, centra horizontalmente y sitúa la base en el suelo.
- Aplica el giro horizontal solicitado y exporta con Y hacia arriba, compatible con glTF/Godot.
- Conserva los materiales compatibles del GLB y comprueba UV, referencias a imágenes y geometría básica.
- La reducción de triángulos es opcional: `0` la desactiva. Otro valor fija un objetivo aproximado y requiere revisión visual.
- Cada exportación crea otra carpeta. El GLB de entrada se conserva.

La orientación frontal se comprueba visualmente: el script no puede adivinar qué lado es la cara. Este flujo prepara mallas estáticas; no crea rig, animaciones, colisiones ni retopología artística. Los archivos con rig o animación se detienen para revisión manual.

## Referencias oficiales

- [Formatos 3D de Godot](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html)
- [Consideraciones de exportación](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/model_export_considerations.html)
- [Exportador glTF de Blender](https://docs.blender.org/api/current/bpy.ops.export_scene.html)
