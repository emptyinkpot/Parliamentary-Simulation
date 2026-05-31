extends Node
## Army management: recruitment, movement, battle, siege, and war exhaustion.

# --- Signals ---

signal army_recruited(army_id: int)
signal army_moved(army_id: int, target_province: int)
signal battle_resolved(attacker_id: int, defender_id: int, attacker_won: bool)
signal siege_completed(army_id: int, province_id: int)

# --- Enums ---

enum MilitaryBranch { ARMY, NAVY }

# --- Constants ---

const BASE_MOVEMENT_DAYS: int = 1
const BASE_MORALE_RECOVERY: float = 2.0
const WAR_EXHAUSTION_PER_BATTLE: float = 5.0
const WAR_EXHAUSTION_PER_MONTH: float = 0.5
const SIEGE_BASE_DAYS_PER_LEVEL: float = 30.0
const RECRUITMENT_POP_CAP: float = 0.1  ## Max 10% of province population

# --- Data Classes ---

class ArmyData:
	var id: int
	var owner_country_id: int
	var province_id: int
	var strength: int
	var morale: float = 100.0       ## 0-100
	var supply: float = 100.0       ## 0-100
	var leader_name: String = ""
	var leader_bonus: float = 0.0   ## 0-1 multiplier
	var branch: int = MilitaryBranch.ARMY


class BattleResult:
	var attacker_losses: int = 0
	var defender_losses: int = 0
	var attacker_won: bool = false
	var morale_shift_attacker: float = 0.0
	var morale_shift_defender: float = 0.0


# --- State ---

var _armies: Dictionary = {}  ## army_id -> ArmyData
var _next_army_id: int = 1


# --- Accessors ---

func get_army(army_id: int) -> ArmyData:
	return _armies.get(army_id)


func get_all_armies() -> Array:
	return _armies.values()


func get_armies_in_province(province_id: int) -> Array:
	var result: Array = []
	for army: ArmyData in _armies.values():
		if army.province_id == province_id:
			result.append(army)
	return result


func get_country_armies(country_id: int) -> Array:
	var result: Array = []
	for army: ArmyData in _armies.values():
		if army.owner_country_id == country_id:
			result.append(army)
	return result


# --- Public API ---

func reset() -> void:
	_armies.clear()
	_next_army_id = 1


## Recruit an army from a province's population (10% cap).
## Returns the new army or null if insufficient population.
func recruit(owner_country_id: int, province_id: int,
		requested_strength: int, province_population: int,
		branch: MilitaryBranch = MilitaryBranch.ARMY,
		leader_name: String = "") -> ArmyData:
	var available := int(province_population * RECRUITMENT_POP_CAP)
	var strength := mini(requested_strength, available)
	if strength <= 0:
		return null

	var army := ArmyData.new()
	army.id = _next_army_id
	army.owner_country_id = owner_country_id
	army.province_id = province_id
	army.strength = strength
	army.morale = 100.0
	army.supply = 100.0
	army.leader_name = leader_name
	army.leader_bonus = 0.1 if not leader_name.is_empty() else 0.0
	army.branch = branch

	_armies[army.id] = army
	_next_army_id += 1
	army_recruited.emit(army.id)
	return army


## Move army to target province. Returns travel days (terrain-modified).
## terrain_modifier: 1.0 = flat, 1.5 = hills, 2.0 = mountains, 0.5 = road
func move_army(army_id: int, target_province_id: int, terrain_modifier: float = 1.0) -> int:
	var army: ArmyData = _armies.get(army_id)
	if army == null:
		return -1
	army.province_id = target_province_id
	army.supply = maxf(0.0, army.supply - 5.0)
	army_moved.emit(army_id, target_province_id)
	return ceili(BASE_MOVEMENT_DAYS * terrain_modifier)


## Resolve a battle between attacker and defender armies.
## terrain_defense_bonus: 0-0.5 extra multiplier for defender.
func resolve_battle(attacker: ArmyData, defender: ArmyData,
		terrain_defense_bonus: float = 0.0) -> BattleResult:
	var atk_power := attacker.strength * (attacker.morale / 100.0) * (1.0 + attacker.leader_bonus)
	var def_power := defender.strength * (defender.morale / 100.0) * (1.0 + defender.leader_bonus + terrain_defense_bonus)

	var total_power := atk_power + def_power
	var result := BattleResult.new()
	if total_power <= 0.0:
		return result

	var atk_ratio := atk_power / total_power
	var def_ratio := def_power / total_power

	result.attacker_losses = roundi(attacker.strength * def_ratio * 0.3)
	result.defender_losses = roundi(defender.strength * atk_ratio * 0.3)

	attacker.strength = maxi(0, attacker.strength - result.attacker_losses)
	defender.strength = maxi(0, defender.strength - result.defender_losses)

	result.attacker_won = atk_power > def_power
	var morale_swing: float = 15.0

	if result.attacker_won:
		result.morale_shift_attacker = morale_swing * 0.5
		result.morale_shift_defender = -morale_swing
	else:
		result.morale_shift_attacker = -morale_swing
		result.morale_shift_defender = morale_swing * 0.5

	attacker.morale = clampf(attacker.morale + result.morale_shift_attacker, 0.0, 100.0)
	defender.morale = clampf(defender.morale + result.morale_shift_defender, 0.0, 100.0)

	battle_resolved.emit(attacker.id, defender.id, result.attacker_won)
	return result


# --- Siege ---

## Calculate siege duration in days based on fortress level (1-10).
func get_siege_duration(fortress_level: int) -> int:
	return roundi(SIEGE_BASE_DAYS_PER_LEVEL * maxi(1, fortress_level))


## Advance siege by one day. Returns true when siege completes.
func advance_siege(fortress_level: int, days_besieged: int) -> bool:
	return (days_besieged + 1) >= get_siege_duration(fortress_level)


# --- War Exhaustion ---

## Calculate accumulated war exhaustion for a country (0-100).
static func calculate_war_exhaustion(battles_count: int, months_at_war: int) -> float:
	return clampf(
		battles_count * WAR_EXHAUSTION_PER_BATTLE + months_at_war * WAR_EXHAUSTION_PER_MONTH,
		0.0, 100.0)


# --- Morale Recovery ---

## Apply daily morale recovery to all armies.
func tick_morale_recovery() -> void:
	for army: ArmyData in _armies.values():
		if army.morale < 100.0:
			army.morale = minf(100.0, army.morale + BASE_MORALE_RECOVERY)


## Remove destroyed armies (strength <= 0).
func cleanup_destroyed() -> void:
	var to_remove: Array[int] = []
	for army_id: int in _armies:
		if _armies[army_id].strength <= 0:
			to_remove.append(army_id)
	for aid: int in to_remove:
		_armies.erase(aid)
