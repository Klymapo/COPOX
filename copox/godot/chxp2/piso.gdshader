shader_type spatial;
render_mode cull_disabled;
// piso de revisión: gris claro con rejilla de 0.05 u y línea fuerte cada 0.25 u (unidades ALTH del GLB)
varying vec3 w;
void vertex() { w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float linea(vec2 p, float paso, float grosor) {
	vec2 g = abs(fract(p / paso - 0.5) - 0.5) * paso;
	vec2 fw = fwidth(p);
	vec2 l = 1.0 - smoothstep(grosor - fw, grosor + fw, g);
	return max(l.x, l.y);
}
void fragment() {
	vec3 base = vec3(0.64, 0.635, 0.68);
	float fino = linea(w.xz, 0.05, 0.0006) * (1.0 - smoothstep(0.0, 0.004, length(fwidth(w.xz))));
	float grueso = linea(w.xz, 0.25, 0.0012);
	ALBEDO = mix(base, vec3(0.50, 0.49, 0.55), max(fino * 0.55, grueso));
	ROUGHNESS = 1.0;
}
