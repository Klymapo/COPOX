---
name: crear-avatar
description: Crea o actualiza un personaje ALTH-META desde una ficha JSON en un solo comando (base congelada de Adán + ropa, pelo y calzado del catálogo + CHXP V3 + publicación). Úsala cuando Admin pida un personaje nuevo (Alastor, ciudadanos) o cambios a uno existente (Theo).
---

# Crear avatar (COPOX)

Reemplaza la cadena de 40+ recetas por: **base congelada + ficha**. Comando:

```
python -m copox.avatar personajes/<nombre>.json [--rapido] [--publicar] [--salida DIR]
```

## Flujo con Admin
1. **Lápiz** (no se construye): lee la referencia (`refs/personajes/…` o Drive). Propón la ficha:
   - prendas y conjunto del catálogo (`copox/medicion/catalogo.py`); si una prenda NO existe → skill
     `investigar-referencias` + research brief antes de inventarla (regla CLAUDE.md);
   - colores SOLO de `spec/alth_spec.json` → paleta (un color nuevo se propone a Admin antes de usarlo);
   - telas (`copox/medicion/texturas_tela.py`), pelo, calzado, manos, holguras.
   Pregunta lo dudoso (Dispara) y espera **Martillo**.
2. **Martillo**: escribe `personajes/<nombre>.json` (ver `personajes/theo.json` como plantilla).
3. Itera con `--rapido` (~1.5 min por vuelta: construir + CHXP sin GIF). Mira las vistas y acercamientos tú mismo
   antes de mandar nada. Máximo **3 iteraciones por método**; sin unanimidad → PLATEAU, conserva la mejor, avisa.
4. Entrega: corrida completa (con GIF) y `--publicar` (skill `publicar-version` hace el resto, incluida la línea de Drive).

## Ficha (campos)
- `nombre`: NOMBRE_VNN del GLB. `base`: null = `ADAN_BASE_CONGELADA.glb` (se verifica su SHA).
- `pelo`, `calzado`, `manos`: claves de `catalogo.PELO/CALZADO/MANOS`. `visible`: overrides de nodos.
- `ropa.conjunto` (`catalogo.ROPA`), `ropa.colores`, `ropa.telas`, `ropa.params.<grupo>` (holguras, cortes…).
- `chxp`: `tipo`, `ref`, `ref_2x2`, `brief`, `gif`. `publicar`: `carpeta`, `nombre`, `nota`, `estado`.
- `sha_esperado` (opcional): para comprobar reproducibilidad.

## Reglas que no se negocian (de LECCIONES.md)
- El pelo cubre toda el área (≥ 99.5 %) y se mueve (resortes). La ropa va por capas, un poco holgada, con textura
  sutil, sin pintar; respeta el límite pantalón/zapato. Nada de colores fuera de paleta.
- No tocar `theo_alpha.glb` ni la base congelada. Toda versión sale SIN APROBAR.
- La prueba de reproducibilidad: `personajes/theo.json` debe dar SHA `74fc6240…` (THEO_VESTIDO_V4_1).
