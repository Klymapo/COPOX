// COPOX · ALTH-META · ojo con mirada (pupila móvil).
// Tres capas en el UV de la placa del ojo: base (esclerótica, alfa = abertura), iris (se desplaza)
// y encima (línea del párpado, fija). El brillo viaja con el iris. El iris nunca sale de la abertura: se recorta con la base.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D tex_base : source_color, filter_linear_mipmap;
uniform sampler2D tex_iris : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D tex_encima : source_color, filter_linear_mipmap;
uniform vec2 mirada = vec2(0.0);            // -1..1: x > 0 mira a la derecha de la imagen (vista de frente), y > 0 arriba
uniform vec2 rango_uv = vec2(0.164, 0.137); // desplazamiento máximo del iris en UV (generar_capas.py)
uniform float rugosidad = 0.65;

void fragment() {
	vec4 b = texture(tex_base, UV);
	if (b.a < 0.5) {
		discard;
	}
	vec2 m = clamp(mirada, vec2(-1.0), vec2(1.0));
	vec2 desplazamiento = vec2(-m.x * rango_uv.x, -m.y * rango_uv.y);  // signos verificados en Godot 4.7.2
	vec4 i = texture(tex_iris, UV - desplazamiento);
	vec3 c = mix(b.rgb, i.rgb, i.a);
	vec4 e = texture(tex_encima, UV);
	c = mix(c, e.rgb, e.a);
	ALBEDO = c;
	ROUGHNESS = rugosidad;
}
