extends Node
## War declaration, war goals, war score, peace negotiation, and state machine.

# --- Signals ---

signal war_declared(war_id: int)
signal war_activated(war_id: int)
signal war_negotiating(war_id: int)
signal war_ended(war_id: int)
signal battle_recorded(war_id: int, attacker_won: bool)

# --- Enums ---

enum WarStatus { PREPARING, ACTIVE, NEGOTIATING, ENDED }

enum CasusBelli { CONQUEST, LIBERATION, SUBJUGATION, HUMILIATION, DEFENSIVE_WAR }

enum WarGoalType { TERRITORY, REPARATIONS, VASSALIZATION }

# --- Constants ---

const TERRITORY_COST: float = 10.0
const REPARATIONS_COST: float = 5.0
const VASSALIZATION_COST: float = 50.0

# --- Data Classes ---

class WarGoal:
	var type: int = WarGoalType.TERRITORY
	var target_province_id: int = -1
	var reparation_amount: float = 0.0

	func _init(p_type: int = WarGoalType.TERRITORY, p_province: int = -1,
			p_amount: float = 0.0) -> void:
		type = p_type
		target_province_id = p_province
		reparation_amount = p_amount

	func get_cost() -> float:
		match type:
			WarGoalType.TERRITORY: return TERRITORY_COST
			WarGoalType.REPARATIONS: return REPARATIONS_COST
			WarGoalType.VASSALIZATION: return VASSALIZATION_COST
		return 0.0


class WarData:
	var id: int
	var name: String
	var attacker_country_id: int
	var defender_country_id: int
	var casus_belli: int  ## CasusBelli enum
	var status: int = WarStatus.PREPARING
	var attacker_goals: Array[WarGoal] = []
	var defender_goals: Array[WarGoal] = []
	var battles_won_by_attacker: int = 0
	var battles_won_by_defender: int = 0
	var provinces_occupied_by_attacker: int = 0
	var provinces_occupied_by_defender: int = 0
	var blockade_score: int = 0
	var months_at_war: int = 0
	var start_date: float = 0.0  ## Unix timestamp


# --- State ---

var _wars: Dictionary = {}  ## war_id -> WarData
var _next_war_id: int = 1


# --- Accessors ---

func get_war(war_id: int) -> WarData:
	return _wars.get(war_id)


func get_active_wars() -> Array:
	var result: Array = []
	for war: WarData in _wars.values():
		if war.status == WarStatus.ACTIVE:
			result.append(war)
	return result


func get_all_wars() -> Array:
	return _wars.values()


# --- Public API ---

func reset() -> void:
	_wars.clear()
	_next_war_id = 1


## Declare war. A casus belli is required. Returns the new war or null.
func declare_war(attacker_id: int, defender_id: int,
		cb: CasusBelli, war_name: String = "") -> WarData:
	if attacker_id == defender_id:
		return null

	var war := WarData.new()
	war.id = _next_war_id
	war.name = war_name if not war_name.is_empty() else "War #%d" % _next_war_id
	war.attacker_country_id = attacker_id
	war.defender_country_id = defender_id
	war.casus_belli = cb
	war.status = WarStatus.PREPARING
	war.start_date = Time.get_unix_time_from_system()

	_wars[war.id] = war
	_next_war_id += 1
	war_declared.emit(war.id)
	return war


## Transition war from Preparing to Active.
func activate_war(war_id: int) -> bool:
	var war: WarData = _wars.get(war_id)
	if war == null or war.status != WarStatus.PREPARING:
		return false
	war.status = WarStatus.ACTIVE
	war_activated.emit(war_id)
	return true


## Record a battle result into the war.
func record_battle(war_id: int, attacker_won: bool) -> void:
	var war: WarData = _wars.get(war_id)
	if war == null:
		return
	if attacker_won:
		war.battles_won_by_attacker += 1
	else:
		war.battles_won_by_defender += 1
	battle_recorded.emit(war_id, attacker_won)


## Calculate war score for the attacker (0-100).
## Defender score = 100 - attacker score.
func calculate_war_score(war: WarData) -> float:
	var battle_score := (war.battles_won_by_attacker - war.battles_won_by_defender) * 10.0
	var occupation_score := (war.provinces_occupied_by_attacker - war.provinces_occupied_by_defender) * 5.0
	var blockade_bonus := war.blockade_score * 2.0
	return clampf(50.0 + battle_score + occupation_score + blockade_bonus, 0.0, 100.0)


## Begin peace negotiations. Transitions Active -> Negotiating.
func begin_negotiation(war_id: int) -> bool:
	var war: WarData = _wars.get(war_id)
	if war == null or war.status != WarStatus.ACTIVE:
		return false
	war.status = WarStatus.NEGOTIATING
	war_negotiating.emit(war_id)
	return true


## Check if a set of demands is acceptable given the current war score.
func can_demand(war: WarData, demands: Array[WarGoal]) -> bool:
	var score := calculate_war_score(war)
	var cost: float = 0.0
	for demand: WarGoal in demands:
		cost += demand.get_cost()
	return score >= cost


## Sign peace and end the war.
func sign_peace(war_id: int) -> bool:
	var war: WarData = _wars.get(war_id)
	if war == null or war.status != WarStatus.NEGOTIATING:
		return false
	war.status = WarStatus.ENDED
	war_ended.emit(war_id)
	return true


## Increment months at war for all active wars. Call once per game month.
func tick_month() -> void:
	for war: WarData in _wars.values():
		if war.status == WarStatus.ACTIVE:
			war.months_at_war += 1
