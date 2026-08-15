extends Node2D

const TILE := 32
const PLAYER_SPEED := 150.0
const PLAYER_SCALE := 0.60
const PLAYER_FRAME := Vector2i(96, 112)
const NPC_INTERACT_RANGE := 74.0
const ATTACK_RANGE := 76.0

var zone := "overworld"
var map_data: Dictionary = {}
var player_position := Vector2.ZERO
var facing := "down"
var walk_distance := 0.0
var walk_frame := 0
var player_hp := 100
var materials: Dictionary = {}
var world_root: Node2D
var floor_layer: LogicalFloor
var ground_meta_layer: Node2D
var actor_layer: Node2D
var foreground_layer: Node2D
var player_root: Node2D
var player_sprite: Sprite2D
var camera: Camera2D
var hud_zone: Label
var hud_status: Label
var hp_fill: ColorRect
var dialogue_panel: PanelContainer
var dialogue_title: Label
var dialogue_body: Label
var npc_nodes: Array[Dictionary] = []
var enemy_nodes: Array[Dictionary] = []
var transition_lock := 0.0

func _ready() -> void:
	_ensure_input_actions()
	_load_materials()
	_build_ui()
	_load_zone("overworld", Vector2.ZERO)

func _ensure_input_actions() -> void:
	var keys := {
		"move_up": [KEY_W, KEY_UP],
		"move_down": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT],
		"move_right": [KEY_D, KEY_RIGHT],
		"interact": [KEY_E, KEY_SPACE],
		"attack": [KEY_F, KEY_J]
	}
	for action in keys:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for code in keys[action]:
			var event := InputEventKey.new()
			event.physical_keycode = code
			InputMap.action_add_event(action, event)

func _load_materials() -> void:
	for key in ["grass", "forest", "cobble", "dirt", "water", "crypt", "soil"]:
		materials[key] = load("res://assets/materials/%s.png" % key)

func _build_ui() -> void:
	var ui := CanvasLayer.new()
	add_child(ui)
	var top_panel := PanelContainer.new()
	top_panel.position = Vector2(18, 16)
	top_panel.size = Vector2(360, 92)
	ui.add_child(top_panel)
	var top_box := VBoxContainer.new()
	top_panel.add_child(top_box)
	var title := Label.new()
	title.text = "BRÉ THIAR  •  WINDOWS PRODUCTION CLIENT"
	title.add_theme_font_size_override("font_size", 16)
	top_box.add_child(title)
	hud_zone = Label.new()
	hud_zone.text = "Loading…"
	top_box.add_child(hud_zone)
	var hp_back := ColorRect.new()
	hp_back.custom_minimum_size = Vector2(220, 10)
	hp_back.color = Color("241717")
	top_box.add_child(hp_back)
	hp_fill = ColorRect.new()
	hp_fill.size = Vector2(220, 10)
	hp_fill.color = Color("a43b32")
	hp_back.add_child(hp_fill)
	var hint := Label.new()
	hint.position = Vector2(18, 674)
	hint.text = "WASD / Arrows move   •   E or Space interact   •   F or J attack   •   F1/F2/F3 QA jumps"
	hint.add_theme_font_size_override("font_size", 14)
	ui.add_child(hint)
	hud_status = Label.new()
	hud_status.position = Vector2(900, 18)
	hud_status.size = Vector2(350, 28)
	hud_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	ui.add_child(hud_status)
	dialogue_panel = PanelContainer.new()
	dialogue_panel.position = Vector2(300, 500)
	dialogue_panel.size = Vector2(680, 150)
	dialogue_panel.visible = false
	ui.add_child(dialogue_panel)
	var dialog_box := VBoxContainer.new()
	dialogue_panel.add_child(dialog_box)
	dialogue_title = Label.new()
	dialogue_title.add_theme_font_size_override("font_size", 18)
	dialog_box.add_child(dialogue_title)
	dialogue_body = Label.new()
	dialogue_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	dialog_box.add_child(dialogue_body)
	var close := Label.new()
	close.text = "Press E / Space to close"
	close.modulate = Color(0.75, 0.75, 0.75)
	dialog_box.add_child(close)

func _load_zone(next_zone: String, destination: Vector2) -> void:
	zone = next_zone
	if world_root != null:
		world_root.queue_free()
	world_root = Node2D.new()
	add_child(world_root)
	floor_layer = LogicalFloor.new()
	floor_layer.z_index = -20
	world_root.add_child(floor_layer)
	ground_meta_layer = Node2D.new()
	ground_meta_layer.z_index = -10
	world_root.add_child(ground_meta_layer)
	actor_layer = Node2D.new()
	actor_layer.y_sort_enabled = true
	world_root.add_child(actor_layer)
	foreground_layer = Node2D.new()
	foreground_layer.z_index = 3000
	world_root.add_child(foreground_layer)
	map_data = _read_json("res://assets/maps/%s.json" % zone)
	floor_layer.configure(map_data, materials)
	_build_ground_meta()
	_build_props()
	_build_npcs()
	_build_enemies()
	_build_player()
	if destination == Vector2.ZERO:
		var entry: Array = map_data.get("entry", [64, 64])
		player_position = Vector2(float(entry[0]), float(entry[1]))
	else:
		player_position = destination
	player_root.position = player_position
	camera.position = player_position
	transition_lock = 0.55
	_update_region_label()
	_status("Loaded %s" % str(map_data.get("name", zone)))

func _read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Unable to open map: %s" % path)
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Invalid map JSON: %s" % path)
		return {}
	return parsed

func _build_ground_meta() -> void:
	if zone != "overworld":
		return
	for item in map_data.get("groundMeta", []):
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.texture = load("res://assets/ground_meta/%s" % str(item.get("sprite", "")))
		sprite.position = Vector2(float(item.get("x", 0)), float(item.get("y", 0)))
		ground_meta_layer.add_child(sprite)

func _build_props() -> void:
	for item in map_data.get("props", []):
		var sprite_name := str(item.get("sprite", ""))
		var group := str(item.get("assetGroup", "props" if zone == "barrow" else "scene_props"))
		var texture: Texture2D = load("res://assets/%s/%s" % [group, sprite_name])
		if texture == null:
			continue
		var root := Node2D.new()
		root.position = Vector2(float(item.get("x", 0)), float(item.get("y", 0)))
		actor_layer.add_child(root)
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.texture = texture
		var scale_value := float(item.get("scale", 1.0))
		sprite.scale = Vector2.ONE * scale_value
		sprite.position = Vector2(-texture.get_width() * scale_value * 0.5, -texture.get_height() * scale_value)
		root.add_child(sprite)
		var foreground_name = item.get("foreground", null)
		if foreground_name != null and str(foreground_name) != "":
			var fg_group := str(item.get("foregroundGroup", "foreground"))
			var fg_texture: Texture2D = load("res://assets/%s/%s" % [fg_group, str(foreground_name)])
			if fg_texture != null:
				var fg := Sprite2D.new()
				fg.centered = false
				fg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
				fg.texture = fg_texture
				fg.scale = Vector2.ONE * scale_value
				fg.position = Vector2(float(item.get("x", 0)) - fg_texture.get_width() * scale_value * 0.5, float(item.get("y", 0)) - fg_texture.get_height() * scale_value)
				foreground_layer.add_child(fg)

func _build_npcs() -> void:
	npc_nodes.clear()
	for item in map_data.get("npcs", []):
		var texture: Texture2D = load("res://assets/npcs/%s" % str(item.get("sprite", "")))
		if texture == null:
			continue
		var root := Node2D.new()
		root.position = Vector2(float(item.get("x", 0)), float(item.get("y", 0)))
		actor_layer.add_child(root)
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.texture = texture
		sprite.position = Vector2(-texture.get_width() * 0.5, -texture.get_height())
		root.add_child(sprite)
		npc_nodes.append({"node": root, "data": item})

func _build_enemies() -> void:
	enemy_nodes.clear()
	for item in map_data.get("enemies", []):
		var enemy_type := str(item.get("type", ""))
		var texture_path := "res://assets/enemies/%s.png" % enemy_type
		var frame_size := Vector2i.ZERO
		if enemy_type == "boar":
			texture_path = "res://assets/characters/boar_clean.png"
			frame_size = Vector2i(96, 96)
		elif enemy_type == "shade":
			texture_path = "res://assets/enemies/ghost.png"
		var texture: Texture2D = load(texture_path)
		if texture == null:
			continue
		var root := Node2D.new()
		root.position = Vector2(float(item.get("x", 0)), float(item.get("y", 0)))
		actor_layer.add_child(root)
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.texture = texture
		var draw_w := texture.get_width()
		var draw_h := texture.get_height()
		if frame_size != Vector2i.ZERO:
			sprite.region_enabled = true
			sprite.region_rect = Rect2(0, 0, frame_size.x, frame_size.y)
			draw_w = frame_size.x
			draw_h = frame_size.y
		var enemy_scale := 0.62 if enemy_type == "boar" else 0.55
		if enemy_type == "warden":
			enemy_scale = 0.46
		sprite.scale = Vector2.ONE * enemy_scale
		sprite.position = Vector2(-draw_w * enemy_scale * 0.5, -draw_h * enemy_scale)
		root.add_child(sprite)
		var enemy_state := item.duplicate(true)
		enemy_state["current_hp"] = int(item.get("hp", 1))
		enemy_state["dead"] = false
		enemy_nodes.append({"node": root, "sprite": sprite, "data": enemy_state})

func _build_player() -> void:
	player_root = Node2D.new()
	actor_layer.add_child(player_root)
	player_sprite = Sprite2D.new()
	player_sprite.centered = false
	player_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	player_sprite.texture = load("res://assets/characters/player_walk_v05.png")
	player_sprite.region_enabled = true
	player_sprite.region_rect = Rect2(0, 0, PLAYER_FRAME.x, PLAYER_FRAME.y)
	player_sprite.scale = Vector2.ONE * PLAYER_SCALE
	player_sprite.position = Vector2(-PLAYER_FRAME.x * PLAYER_SCALE * 0.5, -PLAYER_FRAME.y * PLAYER_SCALE)
	player_root.add_child(player_sprite)
	camera = Camera2D.new()
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 8.0
	camera.zoom = Vector2(1.08, 1.08)
	player_root.add_child(camera)
	camera.make_current()

func _physics_process(delta: float) -> void:
	if dialogue_panel.visible:
		if Input.is_action_just_pressed("interact"):
			dialogue_panel.visible = false
		return
	if transition_lock > 0.0:
		transition_lock -= delta
	var input_vec := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if abs(input_vec.x) > abs(input_vec.y):
		input_vec.y = 0.0
	elif abs(input_vec.y) > 0.0:
		input_vec.x = 0.0
	input_vec = input_vec.normalized()
	if input_vec != Vector2.ZERO:
		_update_facing(input_vec)
		var next := player_position + input_vec * PLAYER_SPEED * delta
		if _position_is_walkable(next):
			player_position = next
			player_root.position = player_position
			walk_distance += PLAYER_SPEED * delta
			walk_frame = int(walk_distance / 14.0) % 4
	else:
		walk_frame = 0
	_update_player_frame()
	_update_region_label()
	_check_transition()
	if Input.is_action_just_pressed("interact"):
		_interact()
	if Input.is_action_just_pressed("attack"):
		_attack()
	if Input.is_key_pressed(KEY_F1):
		_qa_jump("overworld", Vector2(764, 2058))
	elif Input.is_key_pressed(KEY_F2):
		_qa_jump("overworld", Vector2(800, 680))
	elif Input.is_key_pressed(KEY_F3):
		_qa_jump("barrow", Vector2(1040, 1328))

func _update_facing(v: Vector2) -> void:
	if abs(v.x) > abs(v.y):
		facing = "right" if v.x > 0 else "left"
	else:
		facing = "down" if v.y > 0 else "up"

func _update_player_frame() -> void:
	var row := {"down": 0, "left": 1, "right": 2, "up": 3}.get(facing, 0)
	player_sprite.region_rect = Rect2(walk_frame * PLAYER_FRAME.x, int(row) * PLAYER_FRAME.y, PLAYER_FRAME.x, PLAYER_FRAME.y)

func _position_is_walkable(pos: Vector2) -> bool:
	var width := int(map_data.get("width", 0))
	var height := int(map_data.get("height", 0))
	var collision: Array = map_data.get("collision", [])
	for probe in [Vector2(-8, -4), Vector2(8, -4), Vector2(-8, 4), Vector2(8, 4)]:
		var p := pos + probe
		var tx := int(floor(p.x / TILE))
		var ty := int(floor(p.y / TILE))
		if tx < 0 or ty < 0 or tx >= width or ty >= height:
			return false
		var i := ty * width + tx
		if i < 0 or i >= collision.size() or int(collision[i]) != 0:
			return false
	return true

func _check_transition() -> void:
	if transition_lock > 0.0:
		return
	for item in map_data.get("transitions", []):
		var r: Array = item.get("rect", [])
		if r.size() < 4:
			continue
		var rect := Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
		if rect.has_point(player_position):
			var dest: Array = item.get("dest", [64, 64])
			_load_zone(str(item.get("to", "overworld")), Vector2(float(dest[0]), float(dest[1])))
			return

func _interact() -> void:
	var best: Dictionary = {}
	var best_distance := NPC_INTERACT_RANGE
	for entry in npc_nodes:
		var node: Node2D = entry["node"]
		var distance := player_position.distance_to(node.position)
		if distance < best_distance:
			best = entry
			best_distance = distance
	if best.is_empty():
		_status("No one close enough to speak with.")
		return
	var data: Dictionary = best["data"]
	var id := str(data.get("id", ""))
	var lines := {
		"maelith": "The old roads remember every traveler. Rowanwood remembers those who do not return.",
		"eira": "Every Path begins with a choice. The road north is not as quiet as it looks.",
		"brannoc": "Keep your blade ready beyond the village fences.",
		"siofra": "Listen to the stones before you speak. The Barrow has been restless."
	}
	dialogue_title.text = "%s  •  %s" % [str(data.get("name", "Villager")), str(data.get("role", ""))]
	dialogue_body.text = str(lines.get(id, "They have nothing to say just yet."))
	dialogue_panel.visible = true

func _attack() -> void:
	var best: Dictionary = {}
	var best_distance := ATTACK_RANGE
	for entry in enemy_nodes:
		var data: Dictionary = entry["data"]
		if bool(data.get("dead", false)):
			continue
		var node: Node2D = entry["node"]
		var distance := player_position.distance_to(node.position)
		if distance < best_distance:
			best = entry
			best_distance = distance
	if best.is_empty():
		_status("No enemy in reach.")
		return
	var data: Dictionary = best["data"]
	var hp := max(0, int(data.get("current_hp", 1)) - 22)
	data["current_hp"] = hp
	if hp <= 0:
		data["dead"] = true
		best["node"].visible = false
		_status("%s defeated." % str(data.get("name", "Enemy")))
	else:
		_status("%s  %d/%d HP" % [str(data.get("name", "Enemy")), hp, int(data.get("hp", hp))])

func _update_region_label() -> void:
	for item in map_data.get("subregions", []):
		var r: Array = item.get("rect", [])
		if r.size() >= 4 and Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])).has_point(player_position):
			hud_zone.text = str(item.get("name", map_data.get("name", zone)))
			return
	hud_zone.text = str(map_data.get("name", zone))

func _qa_jump(next_zone: String, destination: Vector2) -> void:
	if zone != next_zone:
		_load_zone(next_zone, destination)
	else:
		player_position = destination
		player_root.position = destination
		camera.position = destination
		transition_lock = 0.5
	_update_region_label()

func _status(text: String) -> void:
	hud_status.text = text
	var timer := get_tree().create_timer(2.2)
	timer.timeout.connect(func():
		if hud_status.text == text:
			hud_status.text = ""
	)
