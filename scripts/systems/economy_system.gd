extends Node
## Autoload singleton handling monthly economic calculations.

signal taxes_collected(country_id: int, amount: float)
signal budget_allocated(country_id: int)
signal gdp_calculated(country_id: int, gdp: float)

const BASE_TAX_RATE: float = 0.01
const INFLATION_DECAY: float = 0.98
const INFLATION_PER_INCOME_UNIT: float = 0.001

## Per-country economic state
var country_gdp: Dictionary = {}  # {int: float}
var country_inflation: Dictionary = {}  # {int: float}
var country_monthly_income: Dictionary = {}  # {int: float}


func _ready() -> void:
	pass


## Called each month by the bootstrap/game manager connection.
func process_monthly_tick() -> void:
	var countries := CountryData.get_all()
	for country in countries:
		_process_country_economy(country as CountryData)


func _process_country_economy(country: CountryData) -> void:
	var total_tax_income := _collect_taxes(country)
	country_monthly_income[country.id] = total_tax_income

	_allocate_budget(country, total_tax_income)
	_calculate_gdp(country)
	_update_inflation(country, total_tax_income)


func _collect_taxes(country: CountryData) -> float:
	var total: float = 0.0

	for pid in country.owned_province_ids:
		var province := ProvinceData.get_by_id(pid)
		if province == null:
			continue
		# Tax formula: population * development * base_tax_rate * province_tax_modifier
		var income := province.population * province.development * BASE_TAX_RATE * province.tax
		total += income

	country.treasury += total
	taxes_collected.emit(country.id, total)
	return total


func _allocate_budget(country: CountryData, income: float) -> void:
	# Budget allocation is tracked but not yet consumed by subsystems
	# Future: feed into military upkeep, construction queue, etc.
	var _military := income * country.budget_military
	var _admin := income * country.budget_admin
	var _construction := income * country.budget_construction
	var _research := income * country.budget_research
	var _welfare := income * country.budget_welfare
	budget_allocated.emit(country.id)


func _calculate_gdp(country: CountryData) -> void:
	var gdp: float = 0.0
	for pid in country.owned_province_ids:
		var province := ProvinceData.get_by_id(pid)
		if province:
			gdp += province.population * province.development * province.tax
	country_gdp[country.id] = gdp
	gdp_calculated.emit(country.id, gdp)


func _update_inflation(country: CountryData, income: float) -> void:
	var current: float = country_inflation.get(country.id, 0.0)
	# Inflation grows with income, decays over time
	current = current * INFLATION_DECAY + income * INFLATION_PER_INCOME_UNIT
	country_inflation[country.id] = current


func get_gdp(country_id: int) -> float:
	return country_gdp.get(country_id, 0.0)


func get_inflation(country_id: int) -> float:
	return country_inflation.get(country_id, 0.0)


func get_monthly_income(country_id: int) -> float:
	return country_monthly_income.get(country_id, 0.0)
