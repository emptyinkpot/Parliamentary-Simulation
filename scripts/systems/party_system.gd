class_name PartySystem
extends Node
## Manages political parties: creation, dissolution, spectrum, and coalitions.

# --- Signals ---

signal party_created(party_id: String)
signal party_established(party_id: String)
signal party_dissolved(party_id: String, reason: String)
signal member_joined(party_id: String, member_id: String)
signal member_left(party_id: String, member_id: String)
signal leader_changed(party_id: String, new_leader_id: String)
signal coalition_formed(coalition_id: String)

# --- Constants ---

const REQUIRED_SUPPORTERS: int = 15
const FORMING_DURATION_DAYS: int = 7
const NAME_MIN_LENGTH: int = 2
const NAME_MAX_LENGTH: int = 20
const MANIFESTO_MIN_LENGTH: int = 50
const MANIFESTO_MAX_LENGTH: int = 500
const MAX_TAGS: int = 5

# --- Data Classes ---

class PoliticalSpectrum:
	var economic: int = 50      ## 0 planned - 100 market
	var political: int = 50     ## 0 democratic - 100 authoritarian
	var social: int = 50        ## 0 liberal - 100 conservative
	var international: int = 50 ## 0 internationalist - 100 nationalist

	func _init(e: int = 50, p: int = 50, s: int = 50, i: int = 50) -> void:
		economic = clampi(e, 0, 100)
		political = clampi(p, 0, 100)
		social = clampi(s, 0, 100)
		international = clampi(i, 0, 100)


class PartyData:
	var id: String
	var name: String
	var abbreviation: String
	var manifesto: String
	var founder_id: String
	var leader_id: String
	var spectrum: PoliticalSpectrum
	var is_established: bool = false
	var created_date: float  ## Unix timestamp
	var expiry_date: float   ## Unix timestamp
	var member_ids: Array[String] = []
	var supporter_ids: Array[String] = []
	var tags: Array[String] = []


class CoalitionData:
	var id: String
	var name: String
	var leader_party_id: String
	var member_party_ids: Array[String] = []


# --- State ---

var _parties: Dictionary = {}         ## party_id -> PartyData
var _member_party: Dictionary = {}    ## member_id -> party_id
var _coalitions: Array[CoalitionData] = []


# --- Public API ---

func reset() -> void:
	_parties.clear()
	_member_party.clear()
	_coalitions.clear()


func get_party(party_id: String) -> PartyData:
	return _parties.get(party_id)


func get_member_party(member_id: String) -> String:
	return _member_party.get(member_id, "")


func get_all_parties() -> Array:
	return _parties.values()


## Creates a party in forming state. Must gather 15 supporters within 7 days.
func create_party(id: String, p_name: String, abbreviation: String,
		manifesto: String, founder_id: String, spectrum: PoliticalSpectrum,
		tags: Array[String] = []) -> PartyData:
	if p_name.length() < NAME_MIN_LENGTH or p_name.length() > NAME_MAX_LENGTH:
		return null
	if manifesto.length() < MANIFESTO_MIN_LENGTH or manifesto.length() > MANIFESTO_MAX_LENGTH:
		return null
	if tags.size() > MAX_TAGS:
		return null
	if _member_party.has(founder_id):
		return null

	var now := Time.get_unix_time_from_system()
	var party := PartyData.new()
	party.id = id
	party.name = p_name
	party.abbreviation = abbreviation
	party.manifesto = manifesto
	party.founder_id = founder_id
	party.leader_id = founder_id
	party.spectrum = spectrum
	party.is_established = false
	party.created_date = now
	party.expiry_date = now + FORMING_DURATION_DAYS * 86400.0
	party.member_ids = [founder_id]
	party.supporter_ids = [founder_id]
	party.tags = tags

	_parties[id] = party
	_member_party[founder_id] = id
	party_created.emit(id)
	return party


## Adds a supporter during forming phase. Auto-establishes at threshold.
func add_supporter(party_id: String, supporter_id: String) -> bool:
	var party: PartyData = _parties.get(party_id)
	if party == null or party.is_established:
		return false
	if Time.get_unix_time_from_system() > party.expiry_date:
		return false
	if supporter_id in party.supporter_ids:
		return false

	party.supporter_ids.append(supporter_id)
	if party.supporter_ids.size() >= REQUIRED_SUPPORTERS:
		party.is_established = true
		party_established.emit(party_id)
	return true


func join_party(party_id: String, member_id: String) -> bool:
	var party: PartyData = _parties.get(party_id)
	if party == null or not party.is_established:
		return false
	if _member_party.has(member_id):
		return false
	party.member_ids.append(member_id)
	_member_party[member_id] = party_id
	member_joined.emit(party_id, member_id)
	return true


func leave_party(member_id: String) -> bool:
	var party_id: String = _member_party.get(member_id, "")
	if party_id.is_empty():
		return false
	var party: PartyData = _parties.get(party_id)
	if party == null:
		return false
	party.member_ids.erase(member_id)
	_member_party.erase(member_id)
	member_left.emit(party_id, member_id)
	return true


func dissolve_party(party_id: String, reason: String = "") -> bool:
	var party: PartyData = _parties.get(party_id)
	if party == null:
		return false
	for mid: String in party.member_ids:
		_member_party.erase(mid)
	_parties.erase(party_id)
	# Remove from coalitions
	for i in range(_coalitions.size() - 1, -1, -1):
		_coalitions[i].member_party_ids.erase(party_id)
		if _coalitions[i].member_party_ids.is_empty():
			_coalitions.remove_at(i)
	party_dissolved.emit(party_id, reason)
	return true


func elect_leader(party_id: String, new_leader_id: String) -> bool:
	var party: PartyData = _parties.get(party_id)
	if party == null:
		return false
	if new_leader_id not in party.member_ids:
		return false
	party.leader_id = new_leader_id
	leader_changed.emit(party_id, new_leader_id)
	return true


## Check and expire parties that failed to gather supporters in time.
func tick_expiry() -> void:
	var now := Time.get_unix_time_from_system()
	var to_dissolve: Array[String] = []
	for party_id: String in _parties:
		var party: PartyData = _parties[party_id]
		if not party.is_established and now > party.expiry_date:
			to_dissolve.append(party_id)
	for pid: String in to_dissolve:
		dissolve_party(pid, "expired")


# --- Coalitions ---

func create_coalition(id: String, coalition_name: String, leader_party_id: String) -> CoalitionData:
	if not _parties.has(leader_party_id):
		return null
	var coalition := CoalitionData.new()
	coalition.id = id
	coalition.name = coalition_name
	coalition.leader_party_id = leader_party_id
	coalition.member_party_ids = [leader_party_id]
	_coalitions.append(coalition)
	coalition_formed.emit(id)
	return coalition


func join_coalition(coalition_id: String, party_id: String) -> bool:
	if not _parties.has(party_id):
		return false
	for coalition in _coalitions:
		if coalition.id == coalition_id:
			if party_id in coalition.member_party_ids:
				return false
			coalition.member_party_ids.append(party_id)
			return true
	return false


func get_coalition(coalition_id: String) -> CoalitionData:
	for coalition in _coalitions:
		if coalition.id == coalition_id:
			return coalition
	return null


# --- Spectrum Labels ---

static func get_economic_label(value: int) -> String:
	if value <= 20: return "计划经济派"
	if value <= 40: return "左翼经济"
	if value <= 60: return "中间派"
	if value <= 80: return "右翼经济"
	return "自由市场派"


static func get_political_label(value: int) -> String:
	if value <= 20: return "民主主义者"
	if value <= 40: return "温和民主"
	if value <= 60: return "中间派"
	if value <= 80: return "威权主义"
	return "绝对权威"


static func get_social_label(value: int) -> String:
	if value <= 20: return "激进自由派"
	if value <= 40: return "自由派"
	if value <= 60: return "温和派"
	if value <= 80: return "保守派"
	return "传统主义者"


static func get_international_label(value: int) -> String:
	if value <= 20: return "国际主义者"
	if value <= 40: return "亲国际派"
	if value <= 60: return "中立派"
	if value <= 80: return "民族主义者"
	return "极端民族主义"
