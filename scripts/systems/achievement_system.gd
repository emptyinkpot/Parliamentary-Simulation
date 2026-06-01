extends Node
## Achievement tracking: rarity tiers, conditions, progress, unlock notifications.
## Ported from AchievementSystem.cs.

# --- Signals ---

signal achievement_unlocked(achievement_id: int, country_id: int)

# --- Enums ---

enum AchievementRarity { COMMON, RARE, EPIC, LEGENDARY }

enum AchievementConditionType {
	OWN_PROVINCES,
	WIN_WARS,
	REACH_GDP,
	COLLECT_TAX,
	BUILD_BUILDINGS,
	TRADE_ROUTES,
	POPULATION_TOTAL,
}

# --- Data Classes ---

class AchievementDefinition:
	var id: int
	var name: String
	var description: String
	var rarity: int             ## AchievementRarity
	var condition_type: int     ## AchievementConditionType
	var threshold: float


class AchievementProgress:
	var achievement_id: int
	var country_id: int
	var current_value: float = 0.0
	var unlocked: bool = false
	var unlocked_on_day: int = -1


# --- State ---

var _definitions: Dictionary = {}  ## id -> AchievementDefinition
var _progress: Array[AchievementProgress] = []
var _next_id: int = 1


# --- Public API ---

func reset() -> void:
	_definitions.clear()
	_progress.clear()
	_next_id = 1


## Register a new achievement definition. Returns assigned ID.
func register(name: String, description: String, rarity: int,
		condition_type: int, threshold: float) -> int:
	var id := _next_id
	_next_id += 1
	var def := AchievementDefinition.new()
	def.id = id
	def.name = name
	def.description = description
	def.rarity = rarity
	def.condition_type = condition_type
	def.threshold = threshold
	_definitions[id] = def
	return id


## Check all achievements for a country and update progress.
## Returns list of newly unlocked achievement ids.
func check_progress(country_id: int, current_day: int) -> Array[int]:
	var newly_unlocked: Array[int] = []

	for id in _definitions:
		var def: AchievementDefinition = _definitions[id]
		var current_value := _evaluate_condition(country_id, def.condition_type)

		var prog := _find_progress(def.id, country_id)
		if prog != null:
			if prog.unlocked:
				continue
			prog.current_value = current_value
			if current_value >= def.threshold:
				prog.unlocked = true
				prog.unlocked_on_day = current_day
				newly_unlocked.append(def.id)
				achievement_unlocked.emit(def.id, country_id)
		else:
			var unlocked := current_value >= def.threshold
			var new_prog := AchievementProgress.new()
			new_prog.achievement_id = def.id
			new_prog.country_id = country_id
			new_prog.current_value = current_value
			new_prog.unlocked = unlocked
			new_prog.unlocked_on_day = current_day if unlocked else -1
			_progress.append(new_prog)
			if unlocked:
				newly_unlocked.append(def.id)
				achievement_unlocked.emit(def.id, country_id)

	return newly_unlocked


## Get progress percentage for a specific achievement (0-100).
func get_progress_percent(achievement_id: int, country_id: int) -> float:
	var def: AchievementDefinition = _definitions.get(achievement_id)
	if def == null:
		return 0.0
	if def.threshold <= 0.0:
		return 100.0
	var prog := _find_progress(achievement_id, country_id)
	var current := prog.current_value if prog else 0.0
	return clampf(current / def.threshold * 100.0, 0.0, 100.0)


## Get all unlocked achievement definitions for a country.
func get_unlocked(country_id: int) -> Array:
	var unlocked_ids: Dictionary = {}
	for p in _progress:
		if p.country_id == country_id and p.unlocked:
			unlocked_ids[p.achievement_id] = true
	var result: Array = []
	for id in _definitions:
		if unlocked_ids.has(id):
			result.append(_definitions[id])
	return result


func get_all_definitions() -> Array:
	return _definitions.values()


func is_unlocked(achievement_id: int, country_id: int) -> bool:
	var prog := _find_progress(achievement_id, country_id)
	return prog != null and prog.unlocked


# --- Private Helpers ---

func _find_progress(achievement_id: int, country_id: int) -> AchievementProgress:
	for p in _progress:
		if p.achievement_id == achievement_id and p.country_id == country_id:
			return p
	return null


func _evaluate_condition(country_id: int, condition_type: int) -> float:
	var country := CountryData.get_by_id(country_id)
	if country == null:
		return 0.0

	match condition_type:
		AchievementConditionType.OWN_PROVINCES:
			return float(country.owned_province_ids.size())

		AchievementConditionType.REACH_GDP:
			return EconomySystem.calculate_gdp(country)

		AchievementConditionType.POPULATION_TOTAL:
			var pop: int = 0
			for pid in country.owned_province_ids:
				var prov := ProvinceData.get_by_id(pid)
				if prov:
					pop += prov.population
			return float(pop)

		AchievementConditionType.COLLECT_TAX:
			return country.treasury

		AchievementConditionType.WIN_WARS:
			# Placeholder: tracked externally
			return 0.0

		AchievementConditionType.BUILD_BUILDINGS:
			var buildings: int = 0
			for pid in country.owned_province_ids:
				buildings += BuildingSystem.get_buildings(pid).size()
			return float(buildings)

		AchievementConditionType.TRADE_ROUTES:
			return float(TradeSystem.get_routes_for_country(country_id).size())

		_:
			return 0.0
