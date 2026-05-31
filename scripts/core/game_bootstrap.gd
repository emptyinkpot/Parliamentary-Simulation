class_name GameBootstrap
extends Node2D
## Attached to Main scene root. Initializes game systems, loads data, creates test entities.

const PROVINCE_CSV_PATH := "res://data/definition.csv"

var provinces_loaded: int = 0
var countries_loaded: int = 0


func _ready() -> void:
	print("[GameBootstrap] Initializing game systems...")
	_load_province_data()
	_create_test_countries()
	_assign_provinces_to_countries()
	_initialize_systems()
	print("[GameBootstrap] Bootstrap complete. %d provinces, %d countries loaded." % [provinces_loaded, countries_loaded])
	# Unpause after initialization
	GameManager.unpause()


func _load_province_data() -> void:
	var provinces := ProvinceData.load_all_from_csv(PROVINCE_CSV_PATH)
	provinces_loaded = provinces.size()
	print("[GameBootstrap] Loaded %d provinces from CSV." % provinces_loaded)


func _create_test_countries() -> void:
	# Create test countries for development
	var country_defs: Array[Dictionary] = [
		{"id": 1, "name": "Byzantium", "color": Color(0.5, 0.0, 0.5), "capital": 1},
		{"id": 2, "name": "Ottomans", "color": Color(0.0, 0.5, 0.0), "capital": 5},
		{"id": 3, "name": "France", "color": Color(0.0, 0.0, 0.8), "capital": 10},
		{"id": 4, "name": "England", "color": Color(0.8, 0.0, 0.0), "capital": 15},
		{"id": 5, "name": "Castile", "color": Color(0.9, 0.8, 0.0), "capital": 20},
	]

	for def in country_defs:
		var country := CountryData.new()
		country.id = def["id"]
		country.country_name = def["name"]
		country.color = def["color"]
		country.capital_province_id = def["capital"]
		CountryData.register(country)

	countries_loaded = CountryData.get_all().size()
	print("[GameBootstrap] Created %d test countries." % countries_loaded)


func _assign_provinces_to_countries() -> void:
	# Distribute loaded provinces among test countries for development
	var all_provinces := ProvinceData.get_all()
	var all_countries := CountryData.get_all()
	if all_countries.is_empty():
		return

	for i in range(all_provinces.size()):
		var province: ProvinceData = all_provinces[i]
		var country: CountryData = all_countries[i % all_countries.size()]
		province.owner_country_id = country.id
		country.owned_province_ids.append(province.id)


func _initialize_systems() -> void:
	# Connect economy system to month tick
	if GameManager:
		GameManager.month_advanced.connect(_on_month_advanced)
	print("[GameBootstrap] Systems initialized.")


func _on_month_advanced(_year: int, _month: int) -> void:
	EconomySystem.process_monthly_tick()
