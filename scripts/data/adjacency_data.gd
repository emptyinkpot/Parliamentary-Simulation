class_name AdjacencyData
extends RefCounted
## Loads and queries province adjacency data from adjacency.json.

static var _adjacency: Dictionary = {}  # {int: Array[int]}


static func load_from_json(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("AdjacencyData: Could not open %s" % path)
		return
	var json := JSON.new()
	json.parse(file.get_as_text())
	var data: Dictionary = json.data
	for key in data:
		_adjacency[int(key)] = data[key]


static func get_neighbors(province_id: int) -> Array:
	return _adjacency.get(province_id, [])


static func are_adjacent(a: int, b: int) -> bool:
	return b in get_neighbors(a)
