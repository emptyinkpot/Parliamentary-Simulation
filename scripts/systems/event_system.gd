extends Node
## Event system: definitions, triggers, chains, random pools, and effects.
## Ported from EventSystem.cs. Func<bool> condition -> Callable.

# --- Signals ---

signal event_triggered(definition_id: int, country_id: int)
signal event_resolved(definition_id: int, option_index: int)

# --- Enums ---

enum EventType {
	POLITICAL, ECONOMIC, MILITARY, DIPLOMATIC, SOCIAL, CULTURAL,
	NATURAL, RELIGIOUS, SCIENTIFIC, COLONIAL, FACTION, IMPERIAL,
}

enum EventImportance { TRIVIAL, MINOR, NORMAL, MAJOR, CRITICAL }

enum EventTriggerType { DATE_BASED, CONDITION_BASED, RANDOM, CHAIN_EVENT }

# --- Data Classes ---

class EventEffect:
	var target_type: String     ## "country", "province"
	var target_id: int
	var stat: String            ## "treasury", "population", "tax", ...
	var delta: float


class EventOption:
	var text: String
	var effects: Array[EventEffect] = []
	var chain_event_id: int = -1   ## -1 if none


class EventDefinition:
	var id: int
	var title: String
	var description: String
	var type: int               ## EventType
	var importance: int         ## EventImportance
	var trigger_type: int       ## EventTriggerType
	var options: Array[EventOption] = []
	var trigger_day: int = -1   ## for DATE_BASED
	var condition: Callable     ## for CONDITION_BASED (returns bool)
	var weight: float = 1.0     ## for RANDOM pool
	var chain_parent_id: int = -1  ## for CHAIN_EVENT, -1 if root


class ActiveEvent:
	var definition_id: int
	var target_country_id: int
	var resolved: bool = false


# --- State ---

var _definitions: Dictionary = {}  ## id -> EventDefinition
var _active_events: Array[ActiveEvent] = []
var _next_id: int = 1
var _current_day: int = 0


# --- Public API ---

func reset() -> void:
	_definitions.clear()
	_active_events.clear()
	_next_id = 1
	_current_day = 0


## Register a new event definition. Returns assigned ID.
func register_event(title: String, description: String,
		type: int, importance: int, trigger_type: int,
		options: Array[EventOption],
		trigger_day: int = -1, condition: Callable = Callable(),
		weight: float = 1.0, chain_parent_id: int = -1) -> int:
	var id := _next_id
	_next_id += 1
	var def := EventDefinition.new()
	def.id = id
	def.title = title
	def.description = description
	def.type = type
	def.importance = importance
	def.trigger_type = trigger_type
	def.options = options
	def.trigger_day = trigger_day
	def.condition = condition
	def.weight = weight
	def.chain_parent_id = chain_parent_id
	_definitions[id] = def
	return id


## Advance the day counter and check for triggered events.
func tick(country_id: int) -> Array[ActiveEvent]:
	_current_day += 1
	var triggered: Array[ActiveEvent] = []

	for id in _definitions:
		var def: EventDefinition = _definitions[id]
		var should_fire := false
		match def.trigger_type:
			EventTriggerType.DATE_BASED:
				should_fire = def.trigger_day == _current_day
			EventTriggerType.CONDITION_BASED:
				should_fire = def.condition.is_valid() and bool(def.condition.call())
			EventTriggerType.RANDOM:
				should_fire = _should_fire_random(def.weight)
			EventTriggerType.CHAIN_EVENT:
				should_fire = false  # fired manually

		if should_fire:
			var active := ActiveEvent.new()
			active.definition_id = def.id
			active.target_country_id = country_id
			active.resolved = false
			_active_events.append(active)
			triggered.append(active)
			event_triggered.emit(def.id, country_id)

	return triggered


## Resolve an active event by option index. Applies effects and fires chains.
func resolve_event(active_event_index: int, option_index: int) -> void:
	if active_event_index < 0 or active_event_index >= _active_events.size():
		return
	var active := _active_events[active_event_index]
	if active.resolved:
		return
	var def: EventDefinition = _definitions.get(active.definition_id)
	if def == null:
		return
	if option_index < 0 or option_index >= def.options.size():
		return

	var option := def.options[option_index]
	for effect in option.effects:
		_apply_effect(effect)

	if option.chain_event_id > 0:
		fire_chain_event(option.chain_event_id, active.target_country_id)

	active.resolved = true
	event_resolved.emit(active.definition_id, option_index)


## Manually fire a chain event for a country.
func fire_chain_event(event_id: int, country_id: int) -> void:
	if not _definitions.has(event_id):
		return
	var active := ActiveEvent.new()
	active.definition_id = event_id
	active.target_country_id = country_id
	active.resolved = false
	_active_events.append(active)


## Pick a random event id from the pool using weighted selection.
func pick_random_event() -> int:
	var pool: Array[EventDefinition] = []
	for id in _definitions:
		var def: EventDefinition = _definitions[id]
		if def.trigger_type == EventTriggerType.RANDOM:
			pool.append(def)
	if pool.is_empty():
		return -1

	var total_weight: float = 0.0
	for def in pool:
		total_weight += def.weight
	var roll := randf() * total_weight
	var cumulative: float = 0.0
	for def in pool:
		cumulative += def.weight
		if roll <= cumulative:
			return def.id
	return pool[pool.size() - 1].id


func get_unresolved_events() -> Array[ActiveEvent]:
	var result: Array[ActiveEvent] = []
	for e in _active_events:
		if not e.resolved:
			result.append(e)
	return result


func get_definition(id: int) -> EventDefinition:
	return _definitions.get(id)


func get_current_day() -> int:
	return _current_day


# --- Private Helpers ---

func _should_fire_random(weight: float) -> bool:
	# Base 1% chance per day, scaled by weight
	return randf() < 0.01 * weight


func _apply_effect(effect: EventEffect) -> void:
	match effect.target_type:
		"country":
			var country := CountryData.get_by_id(effect.target_id)
			if country and effect.stat == "treasury":
				country.treasury += effect.delta
		"province":
			var prov := ProvinceData.get_by_id(effect.target_id)
			if prov:
				if effect.stat == "population":
					prov.population += roundi(effect.delta)
				elif effect.stat == "tax":
					prov.tax += effect.delta
