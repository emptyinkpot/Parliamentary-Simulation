extends Node
## Bicameral parliament: Upper House (90 seats) and Lower House (435 seats).
## Manages bill lifecycle and voting logic.

# --- Signals ---

signal bill_submitted(bill_id: String)
signal vote_cast(bill_id: String, member_id: String, choice: VoteChoice)
signal bill_resolved(bill_id: String, status: BillStatus)

# --- Enums ---

enum Chamber { UPPER, LOWER }
enum PeerType { LIFETIME, MERITORIOUS, IMPERIAL }
enum VoteChoice { SUPPORT, OPPOSE, ABSTAIN }
enum BillStatus { PENDING, VOTING, PASSED, REJECTED }

# --- Constants ---

const UPPER_LIFETIME_SEATS: int = 20
const UPPER_MERITORIOUS_SEATS: int = 40
const UPPER_IMPERIAL_SEATS: int = 30
const UPPER_TOTAL_SEATS: int = 90
const LOWER_TOTAL_SEATS: int = 435
const QUORUM_RATIO: float = 0.5

# --- Data Classes ---

class BillData:
	var id: String
	var title: String
	var content: String
	var proposer_id: String
	var status: int = BillStatus.PENDING  # BillStatus enum value

	func _init(p_id: String = "", p_title: String = "", p_content: String = "", p_proposer: String = "") -> void:
		id = p_id
		title = p_title
		content = p_content
		proposer_id = p_proposer


class VoteTally:
	var support: int = 0
	var oppose: int = 0
	var abstain: int = 0

	var total: int:
		get: return support + oppose + abstain

	func has_quorum(total_seats: int) -> bool:
		return total >= int(total_seats * QUORUM_RATIO)

	func passed() -> bool:
		return total > 0 and support > total * 0.5


# --- State ---

## bill_id -> BillData
var _bills: Dictionary = {}
## bill_id -> { member_id: VoteChoice }
var _votes: Dictionary = {}
## member_id -> Chamber
var _member_chambers: Dictionary = {}


# --- Public API ---

func reset() -> void:
	_bills.clear()
	_votes.clear()
	_member_chambers.clear()


func register_member(member_id: String, chamber: Chamber) -> void:
	_member_chambers[member_id] = chamber


func unregister_member(member_id: String) -> void:
	_member_chambers.erase(member_id)


func get_bill(bill_id: String) -> BillData:
	return _bills.get(bill_id)


func submit_bill(id: String, title: String, content: String, proposer_id: String) -> BillData:
	var bill := BillData.new(id, title, content, proposer_id)
	_bills[id] = bill
	bill_submitted.emit(id)
	return bill


func start_vote(bill_id: String) -> bool:
	var bill: BillData = _bills.get(bill_id)
	if bill == null or bill.status != BillStatus.PENDING:
		return false
	bill.status = BillStatus.VOTING
	_votes[bill_id] = {}
	return true


func cast_vote(bill_id: String, member_id: String, choice: VoteChoice) -> bool:
	var bill: BillData = _bills.get(bill_id)
	if bill == null or bill.status != BillStatus.VOTING:
		return false
	if not _member_chambers.has(member_id):
		return false
	if not _votes.has(bill_id):
		_votes[bill_id] = {}
	_votes[bill_id][member_id] = choice
	vote_cast.emit(bill_id, member_id, choice)
	return true


func get_chamber_tally(bill_id: String, chamber: Chamber) -> VoteTally:
	var tally := VoteTally.new()
	var bill_votes: Dictionary = _votes.get(bill_id, {})
	for member_id: String in bill_votes:
		if _member_chambers.get(member_id, -1) != chamber:
			continue
		match bill_votes[member_id]:
			VoteChoice.SUPPORT:
				tally.support += 1
			VoteChoice.OPPOSE:
				tally.oppose += 1
			VoteChoice.ABSTAIN:
				tally.abstain += 1
	return tally


## Tallies votes for both chambers. Bill passes only if both chambers
## reach quorum and pass with >50% support among votes cast.
func tally_votes(bill_id: String) -> BillStatus:
	var bill: BillData = _bills.get(bill_id)
	if bill == null or bill.status != BillStatus.VOTING:
		return BillStatus.REJECTED

	var upper := get_chamber_tally(bill_id, Chamber.UPPER)
	var lower := get_chamber_tally(bill_id, Chamber.LOWER)

	var upper_quorum := upper.has_quorum(UPPER_TOTAL_SEATS)
	var lower_quorum := lower.has_quorum(LOWER_TOTAL_SEATS)

	var passed := upper_quorum and lower_quorum and upper.passed() and lower.passed()
	bill.status = BillStatus.PASSED if passed else BillStatus.REJECTED
	bill_resolved.emit(bill_id, bill.status)
	return bill.status


func get_all_bills() -> Array:
	return _bills.values()


func get_member_chamber(member_id: String) -> int:
	return _member_chambers.get(member_id, -1)
