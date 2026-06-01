extends Node
## Building construction, effects, slots, and wartime destruction.
## Ported from BuildingSystem.cs. Owns the shared ResourceType/BuildingType enums.

# --- Signals ---

signal construction_started(province_id: int, type: BuildingType)
signal construction_completed(province_id: int, type: BuildingType)
signal building_destroyed(province_id: int)

# --- Enums (shared economy enums live here) ---

enum ResourceType { FOOD, IRON, COAL, OIL, GOLD, LUXURY, MILITARY_SUPPLY }

enum BuildingType { FARM, MINE, FACTORY, PORT, FORTRESS, UNIVERSITY, MARKET, BARRACKS }

# --- Data Classes ---

class BuildingDefinition:
	var type: int                       ## BuildingType
	var cost: float
	var construction_months: int
	var produced_resource: int          ## ResourceType
	var production_bonus: float


class BuildingInstance:
	var province_id: int
	var type: int                       ## BuildingType
	var remaining_months: int           ## 0 = completed
	var destroyed: bool = false


# --- State ---

var _buildings: Array[BuildingInstance] = []
var _definitions: Dictionary = {}  ## BuildingType -> BuildingDefinition


func _ready() -> void:
	_register_defaults()


func _register_defaults() -> void:
	_define(BuildingType.FARM, 50.0, 2, ResourceType.FOOD, 1.5)
	_define(BuildingType.MINE, 80.0, 3, ResourceType.IRON, 2.0)
	_define(BuildingType.FACTORY, 120.0, 4, ResourceType.COAL, 2.5)
	_define(BuildingType.PORT, 100.0, 3, ResourceType.GOLD, 1.0)
	_define(BuildingType.FORTRESS, 200.0, 6, ResourceType.MILITARY_SUPPLY, 1.0)
	_define(BuildingType.UNIVERSITY, 150.0, 5, ResourceType.LUXURY, 0.5)
	_define(BuildingType.MARKET, 60.0, 2, ResourceType.GOLD, 1.5)
	_define(BuildingType.BARRACKS, 90.0, 3, ResourceType.MILITARY_SUPPLY, 2.0)


func _define(type: int, cost: float, months: int, resource: int, bonus: float) -> void:
	var def := BuildingDefinition.new()
	def.type = type
	def.cost = cost
	def.construction_months = months
	def.produced_resource = resource
	def.production_bonus = bonus
	_definitions[type] = def


# --- Public API ---

func reset() -> void:
	_buildings.clear()


## Maximum building slots for a province based on population (development proxy).
func get_max_slots(province_id: int) -> int:
	var prov := ProvinceData.get_by_id(province_id)
	if prov == null:
		return 0
	# 1 slot per 500 population, min 1, max 10
	return clampi(prov.population / 500, 1, 10)


## Current number of buildings (including under construction) in a province.
func get_used_slots(province_id: int) -> int:
	var count: int = 0
	for b in _buildings:
		if b.province_id == province_id and not b.destroyed:
			count += 1
	return count


## Attempt to start construction. Returns true if successful.
func start_construction(province_id: int, type: int, owner_country_id: int) -> bool:
	if not _definitions.has(type):
		return false
	if get_used_slots(province_id) >= get_max_slots(province_id):
		return false
	var country := CountryData.get_by_id(owner_country_id)
	if country == null:
		return false
	var def: BuildingDefinition = _definitions[type]
	if country.treasury < def.cost:
		return false

	country.treasury -= def.cost
	var inst := BuildingInstance.new()
	inst.province_id = province_id
	inst.type = type
	inst.remaining_months = def.construction_months
	inst.destroyed = false
	_buildings.append(inst)
	construction_started.emit(province_id, type)
	return true


## Get all completed buildings in a province.
func get_buildings(province_id: int) -> Array[BuildingInstance]:
	var result: Array[BuildingInstance] = []
	for b in _buildings:
		if b.province_id == province_id and not b.destroyed and b.remaining_months == 0:
			result.append(b)
	return result


## Get production bonus for a resource in a province from completed buildings.
func get_production_bonus(province_id: int, resource: int) -> float:
	var bonus: float = 0.0
	for b in _buildings:
		if b.province_id != province_id or b.destroyed or b.remaining_months > 0:
			continue
		var def: BuildingDefinition = _definitions.get(b.type)
		if def and def.produced_resource == resource:
			bonus += def.production_bonus
	return bonus


## Destroy a random building in a province (war damage).
func destroy_building(province_id: int) -> bool:
	var candidates: Array[int] = []
	for i in _buildings.size():
		var b := _buildings[i]
		if b.province_id == province_id and not b.destroyed:
			candidates.append(i)
	if candidates.is_empty():
		return false
	var idx: int = candidates[randi_range(0, candidates.size() - 1)]
	_buildings[idx].destroyed = true
	building_destroyed.emit(province_id)
	return true


## Monthly tick: advance construction timers.
func tick() -> void:
	for b in _buildings:
		if b.destroyed or b.remaining_months <= 0:
			continue
		b.remaining_months -= 1
		if b.remaining_months == 0:
			construction_completed.emit(b.province_id, b.type)


func get_definition(type: int) -> BuildingDefinition:
	return _definitions.get(type)
