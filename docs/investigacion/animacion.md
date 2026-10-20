# Brief · Animación de cuerpo y cara (cinemáticas y juego)

Fecha: 2026-10-20 · Brief válido: sí · Skill: investigar-referencias · Detalle y fuentes: `docs/RUTA_AAA.md` §6.

## Fuentes
- Godot 4.6 «Inverse kinematics returns» (godotengine.org/article/inverse-kinematics-returns-to-godot-4-6): TwoBoneIK3D,
  SplineIK3D, FABRIK3D/CCDIK3D/JacobianIK3D, LookAtModifier3D, BoneTwistDisperser3D, LimitAngularVelocityModifier3D,
  RetargetModifier3D, SpringBoneSimulator3D. API verificada con `--doctool` de Godot 4.7.2 (20 oct).
- CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu): uso libre. Mixamo: gratis con cuenta, manual, no CC0.
- GVHMR (SIGGRAPH Asia 2024) y MoMask: requieren GPU y dependen de SMPL/HumanML3D (licencias de investigación,
  no comerciales) → descartados para el juego.
- MediaPipe Face Landmarker (Apache 2.0): 52 blendshapes tipo ARKit por cuadro, CPU.
- Rhubarb Lip Sync: CLI local, visemas A–F (+G, H, X); reconocedor PocketSphinx sólo inglés, fonético para español.
- NVIDIA Audio2Face 3D (código abierto, sep 2025): licencia y requisitos por verificar; GPU → futuro.

## Decisiones de técnica
- Cuerpo: IK nativo (`IKNativoALTH`) + mocap CMU retargeteado con corrector chibi (`copox/movimiento/bvh.py`) +
  clips por código existentes (`locomocion.py`). Animación por capas para cine: base → actuación → IK de contacto → resortes.
- Cara: MediaPipe → morphs (`cara_arkit.py`) + Rhubarb → visemas (`labios.py`) + emoción a mano. Faltan en la cara
  actual (para una cara nueva con ARKit, que Admin aprueba): ver `cara_arkit.FALTAN`.
- Lados: ARKit nombra Left/Right desde el actor; morphs _L/_R son del personaje; video selfie → `--espejo`.

## Hallazgos de implementación
- TwoBoneIK3D no se mueve con el brazo/pierna recto (T-pose) si no tiene polo: sin plano de flexión. Polos: rodillas +Z,
  codos −Z (`IKNativoALTH` los crea).
- BVH: el retarget por rotaciones de mundo exige ambos esqueletos en T-pose de reposo; el giro de frente se detecta con el
  vector cadera izquierda → derecha.

## Revisiones
- CHXP: `cinco_dedos`, `pesos_normalizados`, `base_preservada` (clips y morphs conservados), GIF del clip nuevo y revisión
  visual. Un GLB con clip nuevo es versión nueva SIN APROBAR.
