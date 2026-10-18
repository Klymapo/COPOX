# Visor Godot (pruebas de modelos)

Proyecto mínimo de Godot 4.7.2 para ver un GLB tal como lo verá el juego: importador oficial, skin, morphs, clips, color de vértice y materiales de dos caras.

```
cp MODELO.glb theo.glb
godot --headless --path . --import
xvfb-run -a godot --path . -- salida=/ruta/out.png yaw=-35 elev=5 alto=0.55 cy=0.6 tam=512 \
    [clip=Idle-loop t=0.5] [morph=parpado_L:1,boca_abrir:1] [sol=0.12 amb=0.55]
```

- `yaw`, `elev`: grados (misma convención que CHXP). `alto`: alto visible (u) con cámara ortográfica. `cy`: altura del objetivo.
- `clip`: Godot quita el sufijo `-loop` al importar (`Idle-loop` → `Idle`); el visor lo resuelve solo.
- Luz calibrada para que la piel iluminada se vea como su color base (sol 0.12, ambiente 0.55, tonemap lineal).
- En el entorno de Elio corre con Mesa llvmpipe (renderer Compatibilidad); Vulkan no está disponible ahí.
- Los GLB no se suben a este repo.

## Ojos con mirada (shader)

- `ojos/ojo_mirada.gdshader`: tres capas en el UV de la placa del ojo.
  - Base: esclerótica; su alfa es la abertura.
  - Iris: iris, pupila y brillo; es la capa que se desplaza.
  - Encima: línea del párpado.
  - El iris nunca sale de la abertura.
- `ojos/ojos_alth.gd` (`OjosALTH`): reemplaza las placas `C7V2_eye_BAKE_L/R` de un personaje importado. Uso:
  ```gdscript
  var ojos = OjosALTH.new()
  ojos.aplicar($Theo)
  ojos.mirada = Vector2(0.5, 0.2)   # x>0 mira a la derecha de la imagen; y>0 arriba; rango −1..1
  ```
- `ojos/generar_capas.py` regenera las capas con el mismo diseño que la textura horneada en el GLB. El GLB conserva su textura como respaldo para otros programas.
- En el visor: `mirada=x:y`.
- Verificado en Godot 4.7.2 (Compatibilidad): centro, derecha, izquierda, arriba, abajo y diagonal; también con el parpadeo.
