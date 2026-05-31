extends Node
## Manages imperial decrees: issuance, lifecycle, and emergency powers.
## Only the Emperor can issue decrees.

# --- Signals ---

signal decree_issued(decree_id: String)
signal decree_activated(decree_id: String)
signal decree_revoked(decree_id: String)
signal decree_expired(decree_id: String)
signal parliament_suspended(is_suspended: bool)

# --- Enums ---

enum DecreeType {
	APPOINTMENT,       ## 人事任命
	POLICY_CHANGE,     ## 政策变更
	EMERGENCY,         ## 紧急状态
	DIPLOMATIC,        ## 外交指令
	MILITARY,          ## 军事命令
	ECONOMIC,          ## 经济政策
	CULTURAL,          ## 文化教育
	SPECIAL,           ## 特别法令
}

enum DecreeStatus { DRAFT, ACTIVE, EXPIRED, REVOKED }

# --- Constants ---

const DEFAULT_DURATION_DAYS: int = 30
const EMERGENCY_DURATION_DAYS: int = 7
const EMERGENCY_PRIORITY_THRESHOLD: int = 8

# --- Data Classes ---

class DecreeData:
	var id: String
	var title: String
	var content: String
	var type: int           ## DecreeType enum value
	var status: int = DecreeStatus.DRAFT
	var issuer_id: String
	var priority: int       ## 1-10
	var issued_date: float  ## Unix timestamp
	var expiry_date: float  ## 0 means permanent

	func is_emergency() -> bool:
		return type == DecreeType.EMERGENCY

	func suspends_parliament() -> bool:
		return is_emergency() and priority >= EMERGENCY_PRIORITY_THRESHOLD


# --- State ---

var _decrees: Dictionary = {}  ## decree_id -> DecreeData
var _parliament_suspended: bool = false


# --- Accessors ---

var is_parliament_suspended: bool:
	get: return _parliament_suspended


func get_decree(decree_id: String) -> DecreeData:
	return _decrees.get(decree_id)


func get_all_decrees() -> Array:
	return _decrees.values()


func get_active_decrees() -> Array:
	var result: Array = []
	for d: DecreeData in _decrees.values():
		if d.status == DecreeStatus.ACTIVE:
			result.append(d)
	return result


# --- Public API ---

func reset() -> void:
	_decrees.clear()
	_parliament_suspended = false


## Issues a new decree. Duration of -1 uses type default. Duration of 0 is permanent.
func issue_decree(id: String, title: String, content: String,
		type: DecreeType, issuer_id: String, priority: int,
		duration_days: int = -1) -> DecreeData:
	if title.is_empty() or content.is_empty():
		return null
	priority = clampi(priority, 1, 10)

	if duration_days < 0:
		duration_days = EMERGENCY_DURATION_DAYS if type == DecreeType.EMERGENCY else DEFAULT_DURATION_DAYS

	var now := Time.get_unix_time_from_system()
	var decree := DecreeData.new()
	decree.id = id
	decree.title = title
	decree.content = content
	decree.type = type
	decree.status = DecreeStatus.DRAFT
	decree.issuer_id = issuer_id
	decree.priority = priority
	decree.issued_date = now
	decree.expiry_date = now + duration_days * 86400.0 if duration_days > 0 else 0.0

	_decrees[id] = decree
	decree_issued.emit(id)
	return decree


## Activates a draft decree. Emergency decrees with priority >= 8 suspend parliament.
func activate(decree_id: String) -> bool:
	var decree: DecreeData = _decrees.get(decree_id)
	if decree == null or decree.status != DecreeStatus.DRAFT:
		return false
	decree.status = DecreeStatus.ACTIVE
	decree_activated.emit(decree_id)

	if decree.suspends_parliament():
		_parliament_suspended = true
		parliament_suspended.emit(true)
	return true


## Revokes an active decree. Lifts parliament suspension if applicable.
func revoke(decree_id: String) -> bool:
	var decree: DecreeData = _decrees.get(decree_id)
	if decree == null or decree.status != DecreeStatus.ACTIVE:
		return false
	decree.status = DecreeStatus.REVOKED
	decree_revoked.emit(decree_id)

	if decree.is_emergency():
		_recalculate_parliament_suspension()
	return true


## Checks all active decrees for expiry. Call once per game day.
func tick_expiry() -> void:
	var now := Time.get_unix_time_from_system()
	for decree_id: String in _decrees:
		var d: DecreeData = _decrees[decree_id]
		if d.status == DecreeStatus.ACTIVE and d.expiry_date > 0.0 and now >= d.expiry_date:
			d.status = DecreeStatus.EXPIRED
			decree_expired.emit(decree_id)
	_recalculate_parliament_suspension()


func _recalculate_parliament_suspension() -> void:
	var was_suspended := _parliament_suspended
	_parliament_suspended = false
	for d: DecreeData in _decrees.values():
		if d.status == DecreeStatus.ACTIVE and d.suspends_parliament():
			_parliament_suspended = true
			break
	if was_suspended != _parliament_suspended:
		parliament_suspended.emit(_parliament_suspended)
