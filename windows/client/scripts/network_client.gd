extends Node
class_name BreNetworkClient

signal status_changed(text: String)
signal authenticated(account: Dictionary)
signal snapshot_received(snapshot: Dictionary)
signal chat_received(message: Dictionary)
signal event_received(message: Dictionary)
signal connection_closed(code: int, reason: String)

@export var server_http := "http://127.0.0.1:8765"
@export var server_ws := "ws://127.0.0.1:8765/ws"

var token := ""
var username := ""
var socket := WebSocketPeer.new()
var http: HTTPRequest
var pending_http := ""
var was_open := false

func _ready() -> void:
	http = HTTPRequest.new()
	http.timeout = 6.0
	add_child(http)
	http.request_completed.connect(_on_http_completed)
	set_process(true)

func register_account(user: String, password: String, character_name: String) -> Error:
	username = user.strip_edges().to_lower()
	pending_http = "register"
	return _post("/api/register", {"username": username, "password": password, "characterName": character_name})

func login(user: String, password: String) -> Error:
	username = user.strip_edges().to_lower()
	pending_http = "login"
	return _post("/api/login", {"username": username, "password": password})

func connect_with_token(value: String) -> Error:
	token = value
	was_open = false
	status_changed.emit("Connecting to Bré Thiar server…")
	socket = WebSocketPeer.new()
	socket.set_no_delay(true)
	return socket.connect_to_url("%s?token=%s" % [server_ws, token.uri_encode()])

func disconnect_world() -> void:
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		send_input("")
		socket.close(1000, "Client exit")

func send_input(direction: String) -> void:
	var dir_value = direction if direction in ["up", "down", "left", "right"] else null
	_send({"type": "input", "dir": dir_value})

func send_skill(index: int) -> void:
	_send({"type": "skill", "index": index})

func send_interact() -> void:
	_send({"type": "interact"})

func send_chat(text: String) -> void:
	var clean := text.strip_edges()
	if not clean.is_empty():
		_send({"type": "chat", "text": clean})

func send_choice(id: String, value) -> void:
	_send({"type": "choice", "id": id, "value": value})

func send_equip(item_id: String) -> void:
	_send({"type": "equip", "id": item_id})

func send_use_item(item_id: String) -> void:
	_send({"type": "useItem", "id": item_id})

func request_community() -> void:
	_send({"type": "community"})

func send_vote(choice: String) -> void:
	_send({"type": "vote", "choice": choice})

func _post(path: String, payload: Dictionary) -> Error:
	if http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return ERR_BUSY
	status_changed.emit("Contacting server…")
	return http.request(
		server_http + path,
		PackedStringArray(["Content-Type: application/json"]),
		HTTPClient.METHOD_POST,
		JSON.stringify(payload)
	)

func _on_http_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var response = JSON.parse_string(body.get_string_from_utf8())
	if result != HTTPRequest.RESULT_SUCCESS:
		status_changed.emit("Server request failed.")
		return
	if typeof(response) != TYPE_DICTIONARY:
		status_changed.emit("Server returned invalid JSON.")
		return
	if response_code < 200 or response_code >= 300:
		status_changed.emit(str(response.get("error", "Server rejected request.")))
		return
	if pending_http in ["register", "login"]:
		token = str(response.get("token", ""))
		if token.is_empty():
			status_changed.emit("Authentication response did not contain a session token.")
			return
		authenticated.emit(response.get("account", {}))
		connect_with_token(token)
	pending_http = ""

func _process(_delta: float) -> void:
	var state := socket.get_ready_state()
	if state == WebSocketPeer.STATE_CONNECTING or state == WebSocketPeer.STATE_OPEN or state == WebSocketPeer.STATE_CLOSING:
		socket.poll()
		state = socket.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		if not was_open:
			was_open = true
			status_changed.emit("Connected.")
		while socket.get_available_packet_count() > 0:
			var packet := socket.get_packet()
			if not socket.was_string_packet():
				continue
			var parsed = JSON.parse_string(packet.get_string_from_utf8())
			if typeof(parsed) == TYPE_DICTIONARY:
				_dispatch(parsed)
	elif state == WebSocketPeer.STATE_CLOSED and was_open:
		was_open = false
		var code := socket.get_close_code()
		var reason := socket.get_close_reason()
		status_changed.emit("Disconnected from server.")
		connection_closed.emit(code, reason)

func _dispatch(message: Dictionary) -> void:
	match str(message.get("type", "")):
		"snapshot":
			snapshot_received.emit(message)
		"chat":
			chat_received.emit(message)
		"event":
			event_received.emit(message)
		"welcome":
			status_changed.emit("World connection established.")

func _send(payload: Dictionary) -> void:
	if socket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	socket.send_text(JSON.stringify(payload))
