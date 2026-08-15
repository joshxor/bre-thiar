extends Node2D
class_name LogicalFloor

var map_data: Dictionary = {}
var materials: Dictionary = {}
var tile_size := 32

func configure(data: Dictionary, material_textures: Dictionary) -> void:
	map_data = data
	materials = material_textures
	tile_size = int(data.get("tileSize", 32))
	queue_redraw()

func _draw() -> void:
	if map_data.is_empty():
		return
	if str(map_data.get("zone", "")) == "barrow":
		_draw_barrow()
	else:
		_draw_outdoor()

func _draw_outdoor() -> void:
	var width := int(map_data.get("width", 0))
	var height := int(map_data.get("height", 0))
	var base: Array = map_data.get("base", [])
	var surface: Array = map_data.get("surface", [])
	var keys: Dictionary = map_data.get("materialKeys", {})
	var base_keys: Array = keys.get("base", [])
	var surface_keys: Array = keys.get("surface", [])
	for y in range(height):
		for x in range(width):
			var i := y * width + x
			if i >= base.size():
				continue
			var key := "grass"
			var bi := int(base[i])
			if bi >= 0 and bi < base_keys.size():
				key = str(base_keys[bi])
			_draw_material(key, Rect2(x * tile_size, y * tile_size, tile_size, tile_size))
			if i < surface.size():
				var si := int(surface[i])
				if si >= 0 and si < surface_keys.size():
					_draw_material(str(surface_keys[si]), Rect2(x * tile_size, y * tile_size, tile_size, tile_size))

func _draw_barrow() -> void:
	var atlas: Texture2D = load("res://assets/tiles/terrain_atlas.png")
	if atlas == null:
		return
	var width := int(map_data.get("width", 0))
	var height := int(map_data.get("height", 0))
	var columns := int(map_data.get("atlasColumns", 8))
	var ground: Array = map_data.get("ground", [])
	for y in range(height):
		for x in range(width):
			var i := y * width + x
			if i >= ground.size():
				continue
			var id := int(ground[i])
			var src := Rect2((id % columns) * tile_size, (id / columns) * tile_size, tile_size, tile_size)
			draw_texture_rect_region(atlas, Rect2(x * tile_size, y * tile_size, tile_size, tile_size), src)

func _draw_material(key: String, rect: Rect2) -> void:
	var texture: Texture2D = materials.get(key)
	if texture != null:
		draw_texture_rect(texture, rect, true)
