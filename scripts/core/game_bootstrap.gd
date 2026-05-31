extends Node2D
## Attached to Main scene root. Initializes game systems, loads data, assigns provinces.

const PROVINCE_CSV_PATH := "res://map-output/definition.csv"
const COUNTRIES_JSON_PATH := "res://data/countries.json"
const ASSIGNMENTS_JSON_PATH := "res://data/province_assignments.json"

var provinces_loaded: int = 0
var countries_loaded: int = 0


func _ready() -> void:
	print("[GameBootstrap] Initializing game systems...")
	_load_province_data()
	_load_countries()
	_assign_provinces_to_countries()
	_initialize_systems()
	print("[GameBootstrap] Bootstrap complete. %d provinces, %d countries loaded." % [provinces_loaded, countries_loaded])
	GameManager.unpause()


func _load_province_data() -> void:
	var provinces := ProvinceData.load_all_from_csv(PROVINCE_CSV_PATH)
	provinces_loaded = provinces.size()
	print("[GameBootstrap] Loaded %d provinces from CSV." % provinces_loaded)


func _load_countries() -> void:
	var file := FileAccess.open(COUNTRIES_JSON_PATH, FileAccess.READ)
	if file == null:
		push_error("[GameBootstrap] Failed to open %s" % COUNTRIES_JSON_PATH)
		return

	var json_text := file.get_as_text()
	file.close()

	var json := JSON.new()
	var err := json.parse(json_text)
	if err != OK:
		push_error("[GameBootstrap] JSON parse error in countries.json: %s" % json.get_error_message())
		return

	var country_array: Array = json.data
	for def: Dictionary in country_array:
		var country := CountryData.new()
		country.id = int(def["id"])
		country.country_name = str(def["name"])
		var c: Array = def["color"]
		country.color = Color(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
		country.capital_province_id = int(def["capital_province_id"])
		CountryData.register(country)

	countries_loaded = CountryData.get_all().size()
	print("[GameBootstrap] Loaded %d countries from JSON." % countries_loaded)


func _assign_provinces_to_countries() -> void:
	var file := FileAccess.open(ASSIGNMENTS_JSON_PATH, FileAccess.READ)
	if file == null:
		push_error("[GameBootstrap] Failed to open %s" % ASSIGNMENTS_JSON_PATH)
		return

	var json_text := file.get_as_text()
	file.close()

	var json := JSON.new()
	var err := json.parse(json_text)
	if err != OK:
		push_error("[GameBootstrap] JSON parse error in province_assignments.json: %s" % json.get_error_message())
		return

	var data: Dictionary = json.data
	var default_owner: int = int(data["default_owner"])
	var overrides: Dictionary = data.get("overrides", {})

	var all_provinces := ProvinceData.get_all()
	for province: ProvinceData in all_provinces:
		var pid_str := str(province.id)
		var owner_id: int = default_owner
		if overrides.has(pid_str):
			owner_id = int(overrides[pid_str])

		province.owner_country_id = owner_id
		var country := CountryData.get_by_id(owner_id)
		if country:
			country.owned_province_ids.append(province.id)

	# Log assignment summary
	var default_country := CountryData.get_by_id(default_owner)
	var default_name := default_country.country_name if default_country else "?"
	print("[GameBootstrap] Assigned provinces. Default owner: %s (%d). Overrides: %d." % [
		default_name, default_owner, overrides.size()])


func _initialize_systems() -> void:
	if GameManager:
		GameManager.month_advanced.connect(_on_month_advanced)
	print("[GameBootstrap] Systems initialized.")


func _on_month_advanced(_year: int, _month: int) -> void:
	EconomySystem.process_monthly_tick()
