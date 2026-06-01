extends Node
## Comprehensive economy simulation: GDP, taxes, budget, inflation,
## unemployment, and zaibatsu (财阀) influence. Ported from EconomySystem.cs.
## Per-country EconomicState is held here, keyed by country id.

# --- Signals ---

signal taxes_collected(country_id: int, amount: float)
signal budget_allocated(country_id: int)
signal gdp_calculated(country_id: int, gdp: float)
signal state_updated(country_id: int)

# --- Enums ---

enum BudgetCategory { MILITARY, ADMINISTRATION, CONSTRUCTION, RESEARCH, WELFARE }

# --- Constants ---

const BASE_TAX_RATE: float = 0.10
const BASE_INFLATION_THRESHOLD: float = 1.2
const DEFLATION_THRESHOLD: float = 0.8
const BASE_UNEMPLOYMENT_RATE: float = 0.04
const ZAIBATSU_INFLUENCE_CAP: float = 0.30
const EXPENSE_RATIO: float = 0.85       ## 85% of income goes to expenses
const PROVINCE_OUTPUT_MULT: float = 1.5
const GOODS_OUTPUT_RATIO: float = 0.6

# --- Data Classes ---

class EconomicState:
	var gdp: float = 0.0
	var gdp_growth: float = 0.0
	var inflation: float = 0.0
	var unemployment: float = 0.04
	var money_supply: float = 100.0
	var goods_output: float = 100.0
	var tax_rate: float = 0.10
	var national_debt: float = 0.0
	var budget_allocation: Dictionary = {}  ## BudgetCategory -> float (sums to 1.0)


# --- State ---

var _states: Dictionary = {}  ## country_id -> EconomicState


# --- Public API ---

func reset() -> void:
	_states.clear()


func get_state(country_id: int) -> EconomicState:
	if _states.has(country_id):
		return _states[country_id]
	return _init_state(country_id)


func set_tax_rate(country_id: int, rate: float) -> void:
	var state := get_state(country_id)
	state.tax_rate = clampf(rate, 0.0, 1.0)
	state_updated.emit(country_id)


func set_budget_allocation(country_id: int, allocation: Dictionary) -> void:
	var state := get_state(country_id)
	state.budget_allocation = _normalize_budget(allocation)
	budget_allocated.emit(country_id)
	state_updated.emit(country_id)


## Monthly tick: collect taxes, pay expenses, update indicators.
func process_monthly_tick() -> void:
	for country: CountryData in CountryData.get_all():
		var state := get_state(country.id)

		var tax_income := calculate_tax_collection(country, state.tax_rate)
		var gdp := calculate_gdp(country)
		var expenses := _calculate_expenses(country, state)

		country.treasury += tax_income - expenses
		state.gdp = gdp
		state.gdp_growth = (tax_income - expenses) / gdp if gdp > 0.0 else 0.0
		state.money_supply += tax_income
		state.goods_output = gdp * GOODS_OUTPUT_RATIO
		state.inflation = calculate_inflation(state)
		state.unemployment = calculate_unemployment(country, state)

		taxes_collected.emit(country.id, tax_income)
		gdp_calculated.emit(country.id, gdp)
		state_updated.emit(country.id)


# --- GDP ---

func calculate_gdp(country: CountryData) -> float:
	var total: float = 0.0
	for pid in country.owned_province_ids:
		var prov := ProvinceData.get_by_id(pid)
		if prov:
			total += _get_province_output(prov)
	return total


# --- Tax Collection ---

func calculate_tax_collection(country: CountryData, tax_rate: float) -> float:
	var total: float = 0.0
	for pid in country.owned_province_ids:
		var prov := ProvinceData.get_by_id(pid)
		if prov:
			total += prov.population * prov.tax * tax_rate
	return total


# --- Budget ---

func get_budget_spending(country_id: int, total_income: float) -> Dictionary:
	var state := get_state(country_id)
	var spending: Dictionary = {}
	for category in state.budget_allocation:
		spending[category] = total_income * state.budget_allocation[category]
	return spending


# --- Inflation / Deflation ---

func calculate_inflation(state: EconomicState) -> float:
	if state.goods_output <= 0.0:
		return 0.0
	var ratio := state.money_supply / state.goods_output
	if ratio > BASE_INFLATION_THRESHOLD:
		return (ratio - BASE_INFLATION_THRESHOLD) * 10.0
	if ratio < DEFLATION_THRESHOLD:
		return (ratio - DEFLATION_THRESHOLD) * 10.0
	return 0.0


# --- Unemployment ---

func calculate_unemployment(country: CountryData, state: EconomicState) -> float:
	var total_pop: int = 0
	var employed_estimate: int = 0
	for pid in country.owned_province_ids:
		var prov := ProvinceData.get_by_id(pid)
		if prov:
			total_pop += prov.population
			employed_estimate += roundi(prov.population * (1.0 - BASE_UNEMPLOYMENT_RATE))
	if total_pop == 0:
		return 0.0
	var base_rate := 1.0 - float(employed_estimate) / total_pop
	var inflation_penalty := maxf(0.0, state.inflation * 0.01)
	return clampf(base_rate + inflation_penalty, 0.0, 1.0)


# --- Zaibatsu / Corporation Influence ---

## Returns political influence modifier from zaibatsu presence (0..CAP).
func get_zaibatsu_influence(country_id: int, total_zaibatsu_assets: float) -> float:
	var state := get_state(country_id)
	if state.gdp <= 0.0:
		return 0.0
	var ratio := total_zaibatsu_assets / state.gdp
	return clampf(ratio, 0.0, ZAIBATSU_INFLUENCE_CAP)


# --- Private Helpers ---

func _init_state(country_id: int) -> EconomicState:
	var state := EconomicState.new()
	state.budget_allocation = _default_budget()
	_states[country_id] = state
	return state


func _default_budget() -> Dictionary:
	return {
		BudgetCategory.MILITARY: 0.30,
		BudgetCategory.ADMINISTRATION: 0.20,
		BudgetCategory.CONSTRUCTION: 0.20,
		BudgetCategory.RESEARCH: 0.15,
		BudgetCategory.WELFARE: 0.15,
	}


func _normalize_budget(raw: Dictionary) -> Dictionary:
	var sum: float = 0.0
	for category in raw:
		sum += raw[category]
	if sum <= 0.0:
		return _default_budget()
	var result: Dictionary = {}
	for category in raw:
		result[category] = raw[category] / sum
	return result


func _get_province_output(prov: ProvinceData) -> float:
	return prov.population * prov.tax * PROVINCE_OUTPUT_MULT


func _calculate_expenses(country: CountryData, state: EconomicState) -> float:
	var income := calculate_tax_collection(country, state.tax_rate)
	return income * EXPENSE_RATIO


# --- Convenience accessors ---

func get_gdp(country_id: int) -> float:
	return get_state(country_id).gdp


func get_inflation(country_id: int) -> float:
	return get_state(country_id).inflation


func get_unemployment(country_id: int) -> float:
	return get_state(country_id).unemployment
