class_name ProvinceData
extends Resource
## Resource representing a single province with geographic and economic data.

@export var id: int = 0
@export var province_name: String = ""
@export var color: Color = Color.BLACK
@export var center_position: Vector2 = Vector2.ZERO
@export var owner_country_id: int = -1
@export var population: int = 10000
@export var tax: float = 1.0
@export var development: int = 1

## Static registry of all provinces keyed by id
static var _registry: Dictionary = {}  # {int: ProvinceData}
## Color lookup table for province identification from map pixels
static var _color_lookup: Dictionary = {}  # {Color: int}


static func register(province: ProvinceData) -> void:
	_registry[province.id] = province
	_color_lookup[province.color] = province.id


static func get_by_id(province_id: int) -> ProvinceData:
	return _registry.get(province_id, null)


static func get_by_color(col: Color) -> ProvinceData:
	var pid: int = _color_lookup.get(col, -1)
	if pid >= 0:
		return _registry.get(pid, null)
	return null


static func get_all() -> Array:
	return _registry.values()


static func clear_registry() -> void:
	_registry.clear()
	_color_lookup.clear()


## Load all provinces from a CSV file.
## Expected CSV columns: id;r;g;b;name;x;y
static func load_all_from_csv(path: String) -> Array:
	clear_registry()

	if not FileAccess.file_exists(path):
		push_warning("ProvinceData: CSV not found at %s" % path)
		return []

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("ProvinceData: Failed to open %s" % path)
		return []

	# Skip header line
	file.get_line()

	while not file.eof_reached():
		var line := file.get_line().strip_edges()
		if line.is_empty() or line.begins_with("#"):
			continue

		var parts := line.split(";")
		if parts.size() < 5:
			continue

		var province := ProvinceData.new()
		province.id = parts[0].to_int()
		var r := parts[1].to_int()
		var g := parts[2].to_int()
		var b := parts[3].to_int()
		province.color = Color(r / 255.0, g / 255.0, b / 255.0)
		province.province_name = parts[4]

		if parts.size() >= 7:
			province.center_position = Vector2(parts[5].to_float(), parts[6].to_float())

		register(province)

	return _registry.values()
