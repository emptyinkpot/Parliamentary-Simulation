extends Node
## Colony creation, monthly growth, management, and independence movements.
## Ported from ColonySystem.cs. Establishment recorded as a game-day count.

# --- Signals ---

signal colony_created(colony_id: int)
signal independence_movement_started(colony_id: int)
signal independence_granted(colony_id: int)

# --- Constants ---

const REQUIRED_TECH_LEVEL: int = 3
const REQUIRED_NAVAL_POWER: int = 20
const BASE_MONTHLY_GROWTH: float = 2.0
const UNREST_THRESHOLD: float = 60.0
const AUTONOMY_THRESHOLD: float = 30.0

# --- Data Classes ---

class Colony:
	var id: int
	var name: String
	var owner_country_id: int
	var province_id: int
	var progress: float = 0.0          ## 0-100, colony development
	var governor_name: String = ""
	var tax_rate: float = 0.1          ## 0-1
	var autonomy: float = 50.0         ## 0-100
	var unrest: float = 0.0            ## 0-100
	var independence_movement: bool = false
	var established_day: int = 0       ## game-day count at founding


# --- State ---

var _colonies: Dictionary = {}  ## colony_id -> Colony
var _next_colony_id: int = 1


# --- Public API ---

func reset() -> void:
	_colonies.clear()
	_next_colony_id = 1


func get_colony(colony_id: int) -> Colony:
	return _colonies.get(colony_id)


func get_all_colonies() -> Array:
	return _colonies.values()


## Create a colony. Requires tech level and naval power thresholds.
## Returns null if requirements not met.
func create_colony(name: String, owner_country_id: int, province_id: int,
		tech_level: int, naval_power: int, current_day: int = 0) -> Colony:
	if tech_level < REQUIRED_TECH_LEVEL:
		return null
	if naval_power < REQUIRED_NAVAL_POWER:
		return null

	var colony := Colony.new()
	colony.id = _next_colony_id
	_next_colony_id += 1
	colony.name = name
	colony.owner_country_id = owner_country_id
	colony.province_id = province_id
	colony.progress = 0.0
	colony.tax_rate = 0.1
	colony.autonomy = 50.0
	colony.unrest = 0.0
	colony.independence_movement = false
	colony.established_day = current_day
	_colonies[colony.id] = colony
	colony_created.emit(colony.id)
	return colony


## Advance all colonies by one month: grow progress, update unrest.
func monthly_tick() -> void:
	for colony: Colony in _colonies.values():
		# Progress growth (higher autonomy = slower growth for owner)
		var growth_mod := 1.0 - (colony.autonomy / 200.0)
		colony.progress = minf(100.0, colony.progress + BASE_MONTHLY_GROWTH * growth_mod)

		# Unrest increases with high tax and low autonomy
		var unrest_delta := (colony.tax_rate * 10.0) - (colony.autonomy * 0.05)
		colony.unrest = clampf(colony.unrest + unrest_delta, 0.0, 100.0)

		# Independence movement trigger
		var was_movement := colony.independence_movement
		colony.independence_movement = colony.autonomy < AUTONOMY_THRESHOLD and colony.unrest > UNREST_THRESHOLD
		if colony.independence_movement and not was_movement:
			independence_movement_started.emit(colony.id)


# --- Colony Management ---

func set_governor(colony_id: int, governor_name: String) -> void:
	var colony: Colony = _colonies.get(colony_id)
	if colony:
		colony.governor_name = governor_name


func set_tax_rate(colony_id: int, rate: float) -> void:
	var colony: Colony = _colonies.get(colony_id)
	if colony:
		colony.tax_rate = clampf(rate, 0.0, 1.0)


func set_autonomy(colony_id: int, autonomy: float) -> void:
	var colony: Colony = _colonies.get(colony_id)
	if colony:
		colony.autonomy = clampf(autonomy, 0.0, 100.0)


func has_independence_movement(colony_id: int) -> bool:
	var colony: Colony = _colonies.get(colony_id)
	return colony != null and colony.independence_movement


## Grant independence: removes colony from owner's control.
func grant_independence(colony_id: int) -> bool:
	if not _colonies.has(colony_id):
		return false
	_colonies.erase(colony_id)
	independence_granted.emit(colony_id)
	return true
