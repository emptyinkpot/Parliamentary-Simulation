extends Node
## Manages the imperial cabinet: appointments, dismissals, and dissolution.

# --- Signals ---

signal cabinet_formed(pm_id: String)
signal minister_appointed(position: CabinetPosition, member_id: String)
signal minister_dismissed(position: CabinetPosition, member_id: String)
signal cabinet_dissolved()

# --- Enums ---

enum CabinetStatus { ACTIVE, RESIGNED, DISSOLVED }

enum AppointmentType { IMPERIAL, PRIME_MINISTER }

enum CabinetPosition {
	PRIME_MINISTER,
	FOREIGN_MINISTER,
	FINANCE_MINISTER,
	ARMY_MINISTER,
	NAVY_MINISTER,
	HOME_MINISTER,
	JUSTICE_MINISTER,
	EDUCATION_MINISTER,
}

# --- Data Classes ---

class MinisterData:
	var member_id: String
	var name: String
	var position: int       ## CabinetPosition enum value
	var appointed_by: int   ## AppointmentType enum value
	var appointed_date: float
	var ability_score: float  ## 0-100, affects system efficiency

	func _init(p_id: String = "", p_name: String = "", p_pos: int = 0,
			p_by: int = 0, p_ability: float = 50.0) -> void:
		member_id = p_id
		name = p_name
		position = p_pos
		appointed_by = p_by
		appointed_date = Time.get_unix_time_from_system()
		ability_score = clampf(p_ability, 0.0, 100.0)


# --- State ---

var _ministers: Dictionary = {}  ## CabinetPosition -> MinisterData
var _status: int = CabinetStatus.DISSOLVED


# --- Accessors ---

var status: int:
	get: return _status

var ministers: Dictionary:
	get: return _ministers


# --- Public API ---

func reset() -> void:
	_ministers.clear()
	_status = CabinetStatus.DISSOLVED


## Forms a new cabinet with the given PM. Fails if a cabinet is already active.
func form_cabinet(pm_member_id: String, pm_name: String, pm_ability: float) -> bool:
	if _status == CabinetStatus.ACTIVE:
		return false
	_ministers.clear()
	_status = CabinetStatus.ACTIVE

	var pm := MinisterData.new(pm_member_id, pm_name,
			CabinetPosition.PRIME_MINISTER, AppointmentType.IMPERIAL, pm_ability)
	_ministers[CabinetPosition.PRIME_MINISTER] = pm
	cabinet_formed.emit(pm_member_id)
	return true


## Appoints a minister to a position. PM cannot be appointed this way.
func appoint_minister(position: CabinetPosition, member_id: String,
		member_name: String, ability: float,
		appointed_by: AppointmentType = AppointmentType.IMPERIAL) -> bool:
	if _status != CabinetStatus.ACTIVE:
		return false
	if position == CabinetPosition.PRIME_MINISTER:
		return false
	if _ministers.has(position):
		return false

	var minister := MinisterData.new(member_id, member_name,
			position, appointed_by, ability)
	_ministers[position] = minister
	minister_appointed.emit(position, member_id)
	return true


## Dismisses a minister. Dismissing the PM triggers full cabinet dissolution.
func dismiss_minister(position: CabinetPosition) -> bool:
	if _status != CabinetStatus.ACTIVE:
		return false
	if not _ministers.has(position):
		return false

	if position == CabinetPosition.PRIME_MINISTER:
		dissolve_cabinet()
		return true

	var minister: MinisterData = _ministers[position]
	_ministers.erase(position)
	minister_dismissed.emit(position, minister.member_id)
	return true


## Dissolves the entire cabinet (total resignation).
func dissolve_cabinet() -> void:
	_ministers.clear()
	_status = CabinetStatus.DISSOLVED
	cabinet_dissolved.emit()


## Returns all positions that have no minister assigned (excluding PM).
func get_vacant_positions() -> Array[int]:
	var vacant: Array[int] = []
	for pos: int in range(CabinetPosition.FOREIGN_MINISTER, CabinetPosition.EDUCATION_MINISTER + 1):
		if not _ministers.has(pos):
			vacant.append(pos)
	return vacant


## Returns average ability score of all serving ministers (0-100).
## Used as efficiency multiplier for government actions.
func get_cabinet_efficiency() -> float:
	if _ministers.is_empty():
		return 0.0
	var total: float = 0.0
	for minister: MinisterData in _ministers.values():
		total += minister.ability_score
	return total / _ministers.size()


## Returns the minister at a given position, or null if vacant.
func get_minister(position: CabinetPosition) -> MinisterData:
	return _ministers.get(position)


## Returns the PM's member_id, or empty string if no active cabinet.
func get_prime_minister_id() -> String:
	var pm: MinisterData = _ministers.get(CabinetPosition.PRIME_MINISTER)
	return pm.member_id if pm else ""
