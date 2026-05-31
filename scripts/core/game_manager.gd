class_name GameManager
extends Node
## Autoload singleton managing the game clock, speed, and date advancement.

signal day_advanced(year: int, month: int, day: int)
signal month_advanced(year: int, month: int)
signal year_advanced(year: int)

const DAYS_IN_MONTH: Array[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

@export var start_year: int = 1444
@export var start_month: int = 1
@export var start_day: int = 1

var current_year: int = 1444
var current_month: int = 1
var current_day: int = 1

var game_speed: int = 3 : set = set_game_speed
var is_paused: bool = true

## Seconds per tick at each speed level (1=slowest, 5=fastest)
var speed_intervals: Array[float] = [0.0, 2.0, 1.0, 0.5, 0.2, 0.05]

var _tick_accumulator: float = 0.0


func _ready() -> void:
	current_year = start_year
	current_month = start_month
	current_day = start_day


func _process(delta: float) -> void:
	if is_paused or game_speed == 0:
		return

	_tick_accumulator += delta
	var interval := speed_intervals[game_speed]

	while _tick_accumulator >= interval:
		_tick_accumulator -= interval
		_advance_day()


func _advance_day() -> void:
	current_day += 1
	var days_this_month := _get_days_in_month(current_month, current_year)

	if current_day > days_this_month:
		current_day = 1
		current_month += 1

		if current_month > 12:
			current_month = 1
			current_year += 1
			year_advanced.emit(current_year)

		month_advanced.emit(current_year, current_month)

	day_advanced.emit(current_year, current_month, current_day)


func _get_days_in_month(month: int, year: int) -> int:
	if month == 2 and _is_leap_year(year):
		return 29
	return DAYS_IN_MONTH[month - 1]


func _is_leap_year(year: int) -> bool:
	return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


func set_game_speed(value: int) -> void:
	game_speed = clampi(value, 0, 5)


func pause() -> void:
	is_paused = true


func unpause() -> void:
	is_paused = false


func toggle_pause() -> void:
	is_paused = not is_paused


func get_date_string() -> String:
	return "%d/%02d/%02d" % [current_year, current_month, current_day]
