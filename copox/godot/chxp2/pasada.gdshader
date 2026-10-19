shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque;
// CHXP V2 · pasadas de datos: 1 normal (espacio cámara, 0..1), 2 profundidad lineal en RG (16 bits), 3 máscara por pieza
uniform int modo = 1;
uniform vec4 id_color;   // SIN source_color: el valor llega tal cual
uniform float cerca = 0.01;
uniform float lejos = 8.0;
varying vec3 v_pos;
// Compatibility escribe el valor tal cual (sin conversión de color): las pasadas de datos salen exactas al PNG
vec3 crudo(vec3 c) { return c; }
void vertex() { v_pos = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	if (modo == 1) {
		vec3 n = normalize(NORMAL);
		if (!FRONT_FACING) { n = -n; }
		ALBEDO = crudo(n * 0.5 + 0.5);
	} else if (modo == 2) {
		float d = clamp((-v_pos.z - cerca) / (lejos - cerca), 0.0, 1.0);
		float a = floor(d * 255.0) / 255.0;
		float b = fract(d * 255.0);
		ALBEDO = crudo(vec3(a, b, 1.0));
	} else {
		ALBEDO = crudo(id_color.rgb);
	}
}
