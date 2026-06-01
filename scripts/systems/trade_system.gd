extends Node
## Trade routes, resource production, tariffs, and trade node collection.
## Ported from TradeSystem.cs. Uses BuildingSystem.ResourceType for resources.

# --- Enums ---

enum EconomicPolicy { FREE_MARKET, PROTECTIONISM, MERCANTILISM, PLANNED }

# --- Data Classes ---

class TradeRoute:
	var from_province_id: int
	var to_province_id: int
	var resource: int           ## BuildingSystem.ResourceType
	var volume: float
	var active: bool = true


class TradeNode:
	var node_id: int
	var name: String
	var connected_province_ids: Array[int] = []
	var collector_country_id: int
	var total_value: float = 0.0


class ProvinceProduction:
	var province_id: int
	var resource: int           ## BuildingSystem.ResourceType
	var base_output: float


# --- State ---

var _routes: Array[TradeRoute] = []
var _nodes: Dictionary = {}  ## node_id -> TradeNode
var _production: Array[ProvinceProduction] = []
var _country_policies: Dictionary = {}  ## country_id -> EconomicPolicy


# --- Public API ---

func reset() -> void:
	_routes.clear()
	_nodes.clear()
	_production.clear()
	_country_policies.clear()


func set_trade_policy(country_id: int, policy: int) -> void:
	_country_policies[country_id] = policy


func get_trade_policy(country_id: int) -> int:
	return _country_policies.get(country_id, EconomicPolicy.FREE_MARKET)


func add_trade_route(from_province: int, to_province: int, resource: int, volume: float) -> void:
	var route := TradeRoute.new()
	route.from_province_id = from_province
	route.to_province_id = to_province
	route.resource = resource
	route.volume = volume
	route.active = true
	_routes.append(route)


func remove_trade_route(from_province: int, to_province: int) -> void:
	var kept: Array[TradeRoute] = []
	for r in _routes:
		if not (r.from_province_id == from_province and r.to_province_id == to_province):
			kept.append(r)
	_routes = kept


func register_trade_node(node_id: int, name: String, province_ids: Array[int], collector_country_id: int) -> void:
	var node := TradeNode.new()
	node.node_id = node_id
	node.name = name
	node.connected_province_ids = province_ids
	node.collector_country_id = collector_country_id
	node.total_value = 0.0
	_nodes[node_id] = node


func set_province_production(province_id: int, resource: int, base_output: float) -> void:
	var kept: Array[ProvinceProduction] = []
	for p in _production:
		if not (p.province_id == province_id and p.resource == resource):
			kept.append(p)
	_production = kept
	var prod := ProvinceProduction.new()
	prod.province_id = province_id
	prod.resource = resource
	prod.base_output = base_output
	_production.append(prod)


func get_active_routes() -> Array[TradeRoute]:
	var result: Array[TradeRoute] = []
	for r in _routes:
		if r.active:
			result.append(r)
	return result


func get_routes_for_country(country_id: int) -> Array[TradeRoute]:
	var owned: Dictionary = {}
	var country := CountryData.get_by_id(country_id)
	if country:
		for pid in country.owned_province_ids:
			owned[pid] = true
	var result: Array[TradeRoute] = []
	for r in _routes:
		if owned.has(r.from_province_id) or owned.has(r.to_province_id):
			result.append(r)
	return result


## Calculate tariff modifier based on trade policy.
func get_tariff_modifier(country_id: int) -> float:
	match get_trade_policy(country_id):
		EconomicPolicy.FREE_MARKET:
			return 0.0
		EconomicPolicy.PROTECTIONISM:
			return 0.25
		EconomicPolicy.MERCANTILISM:
			return 0.40
		EconomicPolicy.PLANNED:
			return 0.60
		_:
			return 0.0


## Monthly tick: flow resources through trade nodes, apply tariffs.
func tick() -> void:
	# Reset node values
	for nid in _nodes:
		_nodes[nid].total_value = 0.0

	# Accumulate production into trade nodes
	for prod in _production:
		for nid in _nodes:
			var node: TradeNode = _nodes[nid]
			if node.connected_province_ids.has(prod.province_id):
				node.total_value += prod.base_output
				break

	# Apply trade route tariffs
	for route in _routes:
		if not route.active:
			continue
		var dest_owner := _get_province_owner(route.to_province_id)
		var tariff := get_tariff_modifier(dest_owner)
		if tariff > 0.0:
			var dest := CountryData.get_by_id(dest_owner)
			if dest:
				dest.treasury += tariff * route.volume

	# Credit collector countries from trade nodes
	for nid in _nodes:
		var node: TradeNode = _nodes[nid]
		if node.total_value > 0.0:
			var collector := CountryData.get_by_id(node.collector_country_id)
			if collector:
				var tariff := get_tariff_modifier(node.collector_country_id)
				collector.treasury += node.total_value * (0.1 + tariff * 0.05)


# --- Helpers ---

func _get_province_owner(province_id: int) -> int:
	var prov := ProvinceData.get_by_id(province_id)
	if prov:
		return prov.owner_country_id
	return -1
