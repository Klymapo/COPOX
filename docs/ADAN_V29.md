# Adán V29 · boca plana (SIN APROBAR)

- **Decisión de Admin (18 oct 2026):** la piel alrededor de la boca, plana; los gestos (músculos) se conservan.
- **Resultado:** `ADAN_V29.glb`, SHA-256 `013498b9738ad03fa96fcc57300dda7769488a74991a7bba7e1dc8b3152f0e33` (en `Klymapo/copox-modelos`). Receta: `docs/medicion/receta_adan_v29.py ADAN_V22_HABLA.glb ADAN_V29.glb`, reproducible bit a bit (verificado).

## Qué se hizo

- Relleno bi-armónico (Δ²z = 0) dentro de un óvalo alrededor de la boca: la superficie más lisa que se une sin escalón a barbilla, cachetes y base de la nariz. Se quita la cresta del labio de arriba (sobresalía 6 mm·u) y los surcos.
- La pared de adentro de los labios no participa (no jala la superficie); hacia las comisuras se vuelve menos honda en rampa.
- Pulido Taubin en z (la malla es irregular y el relleno dejaba ondas chicas) y alisado de las puntas de la rendija.
- La copa negra se metió detrás de la piel (asomaba 4.6 mm·u en las comisuras).
- Los morphs no se tocan: son desplazamientos sobre el reposo, así que todos los gestos se mueven igual.

## Medidas (SENKU · rugosidad del anillo de la boca contra la mejilla; 1 = igual de liso)

| | V28 | V29 |
|---|---|---|
| reposo | 4.1 | 2.3 |
| boca_sonrisa | 6.8 | 4.8 |
| vis_A | 9.6 | 5.3 |
| vis_E | 6.9 | 3.7 |
| boca_triste | 17.6 | 9.5 |

Perfil al centro: de la barbilla a la nariz la piel sube sin bultos (antes: cresta de 6 mm·u en el labio de arriba).

## Probados y descartados

- Ajuste local de la piel cercana (V26): copiaba la base de la nariz y dejaba un hundido.
- Polinomio global: dejaba un aro en "U" bajo la boca en la orilla del óvalo.

## Pendiente

- En Godot, con el sol y sombras, quedan dos marquitas suaves debajo de las comisuras. Sin sombras no aparecen; en CHXP la geometría ahí es lisa (perfiles medidos sin escalón). Falta ubicar qué las proyecta.
