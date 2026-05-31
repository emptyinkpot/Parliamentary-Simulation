shader_type canvas_item;

uniform sampler2D province_texture : filter_nearest;
uniform sampler2D lookup_texture : filter_nearest;
uniform bool show_political = true;

void fragment() {
	vec4 province_color = texture(province_texture, UV);
	if (!show_political) {
		COLOR = province_color;
		return;
	}
	// Use R and G channels as UV into 256x256 lookup texture.
	// Each province has a unique (R, G) pair; the lookup stores country color there.
	vec2 lookup_uv = vec2(province_color.r, province_color.g);
	vec4 country_color = texture(lookup_texture, lookup_uv);
	// If lookup pixel is black (no mapping), fall back to province color
	if (country_color.a < 0.01) {
		COLOR = province_color;
	} else {
		COLOR = country_color;
	}
}
