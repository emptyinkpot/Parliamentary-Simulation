class_name ProvinceMap
extends Node2D
## Renders the political map via GPU shader and handles province selection.

signal province_clicked(province_id: int)
signal province_hovered(province_id: int)

@export var map_texture_path: String = "res://map-output/provinces.bmp"

enum MapMode { POLITICAL, TERRAIN }

var _base_image: Image = null
var _province_texture: ImageTexture = null
var _lookup_image: Image = null
var _lookup_texture: ImageTexture = null
var _sprite: Sprite2D = null
var _shader_material: ShaderMaterial = null
var _hovered_province_id: int = -1
var _current_mode: MapMode = MapMode.POLITICAL


func _ready() -> void:
	_sprite = Sprite2D.new()
	_sprite.centered = false
	add_child(_sprite)
	_load_map()


func _load_map() -> void:
	var tex = load(map_texture_path)
	if tex == null:
		push_warning("ProvinceMap: Map file not found at %s" % map_texture_path)
		return

	_base_image = tex.get_image()
	if _base_image == null:
		push_error("ProvinceMap: Failed to get image from texture.")
		return

	# Create province texture for the shader
	_province_texture = ImageTexture.create_from_image(_base_image)

	# Build lookup texture and apply shader
	_build_lookup_texture()
	_apply_shader()


func _build_lookup_texture() -> void:
	# Create a 256x256 RGBA image. Pixel at (R, G) holds the country color
	# for the province whose map color has those R and G values.
	_lookup_image = Image.create(256, 256, false, Image.FORMAT_RGBA8)
	# Fill with transparent black (alpha=0 means "no mapping")
	_lookup_image.fill(Color(0, 0, 0, 0))

	for province in ProvinceData.get_all():
		if province.owner_country_id < 0:
			continue
		var country := CountryData.get_by_id(province.owner_country_id)
		if country == null:
			continue
		# Province color R and G channels as integer pixel coordinates
		var px: int = int(round(province.color.r * 255.0))
		var py: int = int(round(province.color.g * 255.0))
		_lookup_image.set_pixel(px, py, Color(country.color.r, country.color.g, country.color.b, 1.0))

	_lookup_texture = ImageTexture.create_from_image(_lookup_image)


func _apply_shader() -> void:
	var shader := load("res://scripts/map/political_map.gdshader") as Shader
	if shader == null:
		push_error("ProvinceMap: Shader not found.")
		return

	_shader_material = ShaderMaterial.new()
	_shader_material.shader = shader
	_shader_material.set_shader_parameter("province_texture", _province_texture)
	_shader_material.set_shader_parameter("lookup_texture", _lookup_texture)
	_shader_material.set_shader_parameter("show_political", _current_mode == MapMode.POLITICAL)

	_sprite.texture = _province_texture
	_sprite.material = _shader_material


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			var province_id := _get_province_at_mouse(event.global_position)
			if province_id >= 0:
				province_clicked.emit(province_id)

	elif event is InputEventMouseMotion:
		var province_id := _get_province_at_mouse(event.global_position)
		if province_id != _hovered_province_id:
			_hovered_province_id = province_id
			if province_id >= 0:
				province_hovered.emit(province_id)


func _get_province_at_mouse(screen_pos: Vector2) -> int:
	if _base_image == null:
		return -1

	var local_pos := get_global_transform().affine_inverse() * screen_pos
	var x := int(local_pos.x)
	var y := int(local_pos.y)

	if x < 0 or y < 0 or x >= _base_image.get_width() or y >= _base_image.get_height():
		return -1

	var pixel_color := _base_image.get_pixel(x, y)
	var province := ProvinceData.get_by_color(pixel_color)
	if province:
		return province.id
	return -1


## Rebuild the lookup texture after province ownership changes.
func refresh_political_map() -> void:
	_build_lookup_texture()
	if _shader_material:
		_shader_material.set_shader_parameter("lookup_texture", _lookup_texture)


## Switch between political and terrain map modes.
func set_map_mode(mode: MapMode) -> void:
	_current_mode = mode
	if _shader_material:
		_shader_material.set_shader_parameter("show_political", mode == MapMode.POLITICAL)


func get_map_mode() -> MapMode:
	return _current_mode
