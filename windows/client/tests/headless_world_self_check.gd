extends SceneTree

var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)

func _run() -> void:
	var packed := load("res://scenes/main.tscn") as PackedScene
	_check(packed != null, "main.tscn did not load as PackedScene")
	if packed == null:
		_finish()
		return

	var game := packed.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame

	_check(game != null, "main scene did not instantiate")
	_check(str(game.get("zone")) == "overworld", "initial zone is not overworld")
	var world := game.get("world_root") as Node2D
	var ground := game.get("ground_meta_layer") as Node2D
	var actors := game.get("actor_layer") as Node2D
	var foreground := game.get("foreground_layer") as Node2D
	var player := game.get("player_root") as Node2D
	var floor_node := game.get("floor_layer")
	_check(world != null, "world root missing")
	_check(ground != null, "ground metatile layer missing")
	_check(actors != null, "actor/prop layer missing")
	_check(foreground != null, "foreground layer missing")
	_check(player != null, "player root missing")
	_check(floor_node != null, "logical floor missing")
	var inventory_buttons = game.get("inventory_buttons")
	_check(typeof(inventory_buttons) == TYPE_DICTIONARY and inventory_buttons.has("sword") and inventory_buttons.has("cloak") and inventory_buttons.has("charm") and inventory_buttons.has("bread") and inventory_buttons.has("potion"), "character inventory/equipment controls were not constructed")
	var camera = game.get("camera") as Camera2D
	_check(camera != null, "player camera missing")
	if camera != null:
		_check(camera.limit_right == 1536 and camera.limit_bottom == 2304, "overworld camera limits do not match authored world bounds")
	if ground != null:
		_check(ground.get_child_count() == 60, "overworld did not build exactly 60 authored ground metatiles")
	if foreground != null:
		_check(foreground.get_child_count() > 0, "overworld did not build visible foreground sprites")
	var npcs = game.get("npc_nodes")
	var enemies = game.get("enemy_nodes")
	_check(typeof(npcs) == TYPE_ARRAY and npcs.size() == 4, "overworld NPC count is not 4")
	_check(typeof(enemies) == TYPE_ARRAY and enemies.size() == 4, "overworld enemy count is not 4")

	game.call("_qa_jump", "barrow", Vector2(1040, 1328))
	await process_frame
	await process_frame
	_check(str(game.get("zone")) == "barrow", "QA zone switch to Old Barrow failed")
	ground = game.get("ground_meta_layer") as Node2D
	foreground = game.get("foreground_layer") as Node2D
	enemies = game.get("enemy_nodes")
	_check(ground != null and ground.get_child_count() == 0, "Barrow should not use outdoor ground metatiles")
	_check(typeof(enemies) == TYPE_ARRAY and enemies.size() == 6, "Old Barrow enemy count is not 6")
	var enemy_index = game.get("enemy_by_id")
	_check(typeof(enemy_index) == TYPE_DICTIONARY and enemy_index.has("stonewarden"), "Stonebound Warden was not constructed")
	camera = game.get("camera") as Camera2D
	if camera != null:
		_check(camera.limit_right == 2048 and camera.limit_bottom == 1536, "Old Barrow camera limits do not match authored world bounds")

	var position := game.get("player_position") as Vector2
	_check(position.distance_to(Vector2(1040, 1328)) < 1.0, "Barrow QA destination is incorrect")
	_check(bool(game.call("_position_is_walkable", position)), "Barrow entry position is not walkable")

	game.call("_qa_jump", "overworld", Vector2(800, 680))
	await process_frame
	await process_frame
	_check(str(game.get("zone")) == "overworld", "QA return to overworld failed")
	position = game.get("player_position") as Vector2
	_check(position.distance_to(Vector2(800, 680)) < 1.0, "Rowanwood QA destination is incorrect")
	_check(bool(game.call("_position_is_walkable", position)), "Rowanwood QA position is not walkable")

	game.queue_free()
	await process_frame
	_finish()

func _finish() -> void:
	if failures.is_empty():
		print("BRE THIAR GODOT HEADLESS WORLD SELF-CHECK PASSED")
		print("overworld native layers: PASS")
		print("Bré Thiar / Rowanwood / Old Barrow construction: PASS")
		print("Stonebound Warden construction: PASS")
		print("inventory controls + authored camera bounds: PASS")
		quit(0)
		return
	printerr("BRE THIAR GODOT HEADLESS WORLD SELF-CHECK FAILED")
	for failure in failures:
		printerr(" - " + failure)
	quit(1)
