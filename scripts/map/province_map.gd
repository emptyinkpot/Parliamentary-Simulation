class_name ProvinceMap
extends Node2D
## Renders the political map and handles province selection via pixel color lookup.

signal province_clicked(province_id: int)
signal province_hovered(province_id: int)

@export var map_texture_path: String = "res://map-output/provinces.bmp"

var _base_image: Image = null
var _political_image: Image = null
var _political_texture: ImageTexture = null
var _sprite: Sprite2D = null
var _hovered_province_id: int = -1


func _ready() -> void:
	_sprite = Sprite2D.new()
	_sprite.centered = false
	add_child(_sprite)
	_load_map()


func _load_map() -> void:
	if not FileAccess.file_exists(map_texture_path):
		push_warning("ProvinceMap: Map file not found at %s" % map_texture_path)
		return

	_base_image = Image.load_from_file(map_texture_path)
	if _base_image == null:
		push_error("ProvinceMap: Failed to load map image.")
		return

	_generate_political_map()


func _generate_political_map() -> void:
	if _base_image == null:
		return

	_political_image = _base_image.duplicate()
	var width := _political_image.get_width()
	var height := _political_image.get_height()

	for y in range(height):
		for x in range(width):
			var pixel_color := _base_image.get_pixel(x, y)
			var province := ProvinceData.get_by_color(pixel_color)
			if province and province.owner_country_id >= 0:
				var country := CountryData.get_by_id(province.owner_country_id)
				if country:
					_political_image.set_pixel(x, y, country.color)

	_political_texture = ImageTexture.create_from_image(_political_image)
	_sprite.texture = _political_texture


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


## Refresh the political map colors (call after ownership changes).
func refresh_political_map() -> void:
	_generate_political_map()
