class_name MapCamera
extends Camera2D
## Camera2D with WASD/arrow panning, mouse drag, and scroll wheel zoom.

@export var pan_speed: float = 800.0
@export var drag_sensitivity: float = 1.0
@export var zoom_speed: float = 0.1
@export var min_zoom: float = 0.2
@export var max_zoom: float = 5.0

var _is_dragging: bool = false
var _drag_start: Vector2 = Vector2.ZERO


func _ready() -> void:
	# Start centered with moderate zoom
	zoom = Vector2(1.0, 1.0)
	make_current()


func _process(delta: float) -> void:
	var direction := Vector2.ZERO

	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_A):
		direction.x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
		direction.x += 1.0
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_W):
		direction.y -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
		direction.y += 1.0

	if direction != Vector2.ZERO:
		# Pan speed is inversely proportional to zoom level
		var effective_speed := pan_speed / zoom.x
		position += direction.normalized() * effective_speed * delta


func _unhandled_input(event: InputEvent) -> void:
	# Mouse drag panning
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_MIDDLE:
			_is_dragging = event.pressed
			_drag_start = event.global_position

		# Scroll wheel zoom
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_zoom_at_point(zoom_speed, event.global_position)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_zoom_at_point(-zoom_speed, event.global_position)

	elif event is InputEventMouseMotion and _is_dragging:
		var delta_drag: Vector2 = (_drag_start - event.global_position) * drag_sensitivity / zoom.x
		position += delta_drag
		_drag_start = event.global_position


func _zoom_at_point(factor: float, mouse_pos: Vector2) -> void:
	var old_zoom := zoom
	var new_zoom_value := clampf(zoom.x + factor, min_zoom, max_zoom)
	zoom = Vector2(new_zoom_value, new_zoom_value)

	# Adjust position so zoom centers on mouse position
	if zoom != old_zoom:
		var viewport_center := get_viewport_rect().size / 2.0
		var mouse_offset := (mouse_pos - viewport_center) / old_zoom
		position += mouse_offset * (1.0 - old_zoom.x / zoom.x)
