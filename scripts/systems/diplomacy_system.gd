class_name DiplomacySystem
extends Node
## Diplomatic relations, actions, alliances, and treaties between countries.

# --- Signals ---

signal relation_changed(country_a: int, country_b: int, new_value: int)
signal treaty_signed(treaty_id: int)
signal treaty_expired(treaty_id: int)
signal diplomatic_action_performed(actor: int, target: int, action: DiplomaticAction)

# --- Enums ---

enum DiplomaticRelation { ALLIANCE, FRIENDLY, NEUTRAL, RIVAL, HOSTILE }

enum TreatyType { NON_AGGRESSION, MILITARY_ALLIANCE, TRADE_AGREEMENT, VASSALAGE, DEFENSIVE_PACT }

enum DiplomaticAction {
	IMPROVE_RELATIONS,
	INSULT,
	WARN,
	GUARANTEE_INDEPENDENCE,
	DECLARE_WAR,
	OFFER_PEACE,
}

# --- Constants ---

const MIN_RELATION: int = -200
const MAX_RELATION: int = 200

# --- Data Classes ---

class RelationData:
	var country_a: int
	var country_b: int
	var value: int = 0  ## -200 to +200

	func get_level() -> int:
		return DiplomacySystem.get_relation_level(value)


class TreatyData:
	var id: int
	var country_a: int
	var country_b: int
	var type: int  ## TreatyType enum
	var signed_date: float
	var expiry_date: float  ## 0 means permanent
	var is_active: bool = true


# --- State ---

var _relations: Dictionary = {}  ## "a_b" key -> RelationData (a < b)
var _treaties: Array[TreatyData] = []
var _next_treaty_id: int = 1


# --- Static Helpers ---

static func get_relation_level(value: int) -> int:
	if value >= 100: return DiplomaticRelation.ALLIANCE
	if value >= 30: return DiplomaticRelation.FRIENDLY
	if value >= -30: return DiplomaticRelation.NEUTRAL
	if value >= -100: return DiplomaticRelation.RIVAL
	return DiplomaticRelation.HOSTILE


static func _make_key(a: int, b: int) -> String:
	return "%d_%d" % [mini(a, b), maxi(a, b)]


# --- Accessors ---

func get_relation_value(country_a: int, country_b: int) -> int:
	var key := _make_key(country_a, country_b)
	var r: RelationData = _relations.get(key)
	return r.value if r else 0


func get_relation(country_a: int, country_b: int) -> RelationData:
	return _relations.get(_make_key(country_a, country_b))


func get_all_treaties() -> Array[TreatyData]:
	return _treaties


func get_active_treaties() -> Array:
	var result: Array = []
	for t: TreatyData in _treaties:
		if t.is_active:
			result.append(t)
	return result


# --- Public API ---

func reset() -> void:
	_relations.clear()
	_treaties.clear()
	_next_treaty_id = 1


func set_relation(country_a: int, country_b: int, value: int) -> void:
	var key := _make_key(country_a, country_b)
	var r: RelationData = _relations.get(key)
	if r == null:
		r = RelationData.new()
		r.country_a = mini(country_a, country_b)
		r.country_b = maxi(country_a, country_b)
		_relations[key] = r
	r.value = clampi(value, MIN_RELATION, MAX_RELATION)
	relation_changed.emit(country_a, country_b, r.value)


func modify_relation(country_a: int, country_b: int, delta: int) -> void:
	var current := get_relation_value(country_a, country_b)
	set_relation(country_a, country_b, current + delta)


## Perform a diplomatic action between two countries.
func perform_action(actor: int, target: int, action: DiplomaticAction) -> void:
	match action:
		DiplomaticAction.IMPROVE_RELATIONS:
			modify_relation(actor, target, 15)
		DiplomaticAction.INSULT:
			modify_relation(actor, target, -30)
		DiplomaticAction.WARN:
			modify_relation(actor, target, -10)
		DiplomaticAction.GUARANTEE_INDEPENDENCE:
			modify_relation(actor, target, 20)
		DiplomaticAction.DECLARE_WAR:
			modify_relation(actor, target, -100)
		DiplomaticAction.OFFER_PEACE:
			modify_relation(actor, target, 25)
	diplomatic_action_performed.emit(actor, target, action)


## Check if two countries have a military alliance.
func are_allied(country_a: int, country_b: int) -> bool:
	var key := _make_key(country_a, country_b)
	for t: TreatyData in _treaties:
		if not t.is_active:
			continue
		if t.type != TreatyType.MILITARY_ALLIANCE and t.type != TreatyType.DEFENSIVE_PACT:
			continue
		if _make_key(t.country_a, t.country_b) == key:
			return true
	return false


## Create a treaty between two countries. duration_months=0 means permanent.
func create_treaty(country_a: int, country_b: int,
		type: TreatyType, duration_months: int = 0) -> TreatyData:
	var treaty := TreatyData.new()
	treaty.id = _next_treaty_id
	treaty.country_a = country_a
	treaty.country_b = country_b
	treaty.type = type
	treaty.signed_date = Time.get_unix_time_from_system()
	treaty.expiry_date = treaty.signed_date + duration_months * 30.0 * 86400.0 if duration_months > 0 else 0.0
	treaty.is_active = true

	_treaties.append(treaty)
	_next_treaty_id += 1
	modify_relation(country_a, country_b, 30)
	treaty_signed.emit(treaty.id)
	return treaty


## Expire treaties that have passed their expiry date. Call periodically.
func expire_treaties() -> void:
	var now := Time.get_unix_time_from_system()
	for t: TreatyData in _treaties:
		if t.is_active and t.expiry_date > 0.0 and now >= t.expiry_date:
			t.is_active = false
			treaty_expired.emit(t.id)


# --- Initial 11 Countries Setup ---
## Country IDs: JPN=1, CHN=2, KOR=3, RUS=4, GBR=5, FRA=6, DEU=7, USA=8, OTT=9, AUH=10, ITA=11

func initialize_default_relations() -> void:
	_relations.clear()
	# Japan's starting relations
	set_relation(1, 5, 50)    # JPN-GBR: Friendly (Anglo-Japanese Alliance)
	set_relation(1, 4, -60)   # JPN-RUS: Rival
	set_relation(1, 2, -40)   # JPN-CHN: Rival
	set_relation(1, 3, -80)   # JPN-KOR: Hostile (colonial tension)
	set_relation(1, 7, 20)    # JPN-DEU: Slightly positive
	set_relation(1, 8, 10)    # JPN-USA: Neutral-positive
	set_relation(1, 6, 15)    # JPN-FRA: Neutral-positive
	# European relations
	set_relation(5, 6, 40)    # GBR-FRA: Friendly (Entente Cordiale)
	set_relation(5, 7, -50)   # GBR-DEU: Rival (naval race)
	set_relation(6, 4, 60)    # FRA-RUS: Friendly (Franco-Russian Alliance)
	set_relation(6, 7, -70)   # FRA-DEU: Rival
	set_relation(7, 10, 80)   # DEU-AUH: Allied (Dual Alliance)
	set_relation(7, 9, 30)    # DEU-OTT: Friendly
	set_relation(4, 9, -50)   # RUS-OTT: Rival
	set_relation(10, 9, -30)  # AUH-OTT: Rival (Balkans)
	set_relation(10, 4, -40)  # AUH-RUS: Rival (Balkans)
	# Weak powers
	set_relation(2, 5, -60)   # CHN-GBR: Rival (Opium Wars legacy)
	set_relation(2, 4, -30)   # CHN-RUS: Rival (Manchuria)
