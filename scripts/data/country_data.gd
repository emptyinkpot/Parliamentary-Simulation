class_name CountryData
extends Resource
## Resource representing a country/nation with political and economic data.

@export var id: int = 0
@export var country_name: String = ""
@export var color: Color = Color.GRAY
@export var capital_province_id: int = -1
@export var treasury: float = 100.0
@export var owned_province_ids: Array[int] = []

## Budget allocation percentages (must sum to 1.0)
@export var budget_military: float = 0.3
@export var budget_admin: float = 0.2
@export var budget_construction: float = 0.2
@export var budget_research: float = 0.15
@export var budget_welfare: float = 0.15

## Static registry of all countries keyed by id
static var _registry: Dictionary = {}  # {int: CountryData}


static func register(country: CountryData) -> void:
	_registry[country.id] = country


static func get_by_id(country_id: int) -> CountryData:
	return _registry.get(country_id, null)


static func get_all() -> Array:
	return _registry.values()


static func clear_registry() -> void:
	_registry.clear()


func get_total_population() -> int:
	var total: int = 0
	for pid in owned_province_ids:
		var province := ProvinceData.get_by_id(pid)
		if province:
			total += province.population
	return total


func get_province_count() -> int:
	return owned_province_ids.size()
