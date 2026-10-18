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
