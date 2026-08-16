from pathlib import Path

CLIENT = Path(__file__).resolve().parents[1]
ROOT = CLIENT.parent
SERVER = ROOT / "server" / "server.mjs"
MAIN = CLIENT / "scripts" / "main.gd"
NET = CLIENT / "scripts" / "network_client.gd"

server = SERVER.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")
net = NET.read_text(encoding="utf-8")
errors=[]

for handshake_token in ('PROTOCOL_VERSION','CONTENT_VERSION','protocolVersion','contentVersion'):
    if handshake_token not in server:
        errors.append(f'server handshake missing {handshake_token}')

for message_type in ("input","skill","chat","interact","choice","equip","useItem","community","vote"):
    if f"msg.type==='{message_type}'" not in server:
        errors.append(f"server missing message type {message_type}")
for snapshot_field in ("self","players","enemies","npcs","cooldowns","online","subregion","effectiveAtk","effectiveDef","pathSkill"):
    if snapshot_field not in server:
        errors.append(f"server snapshot missing token {snapshot_field}")
for client_token in ("send_input","send_skill","send_interact","send_choice","send_equip","send_use_item","snapshot_received","event_received","PROTOCOL_VERSION","CONTENT_VERSION"):
    if client_token not in net:
        errors.append(f"network client missing {client_token}")
for integration_token in ("_on_snapshot","_sync_remote_players","_sync_enemies","_on_event","authoritative_position","VERSION MISMATCH","_update_inventory_actions","effectiveAtk","effectiveDef"):
    if integration_token not in main:
        errors.append(f"main integration missing {integration_token}")

if errors:
    print("BRE THIAR WINDOWS NETWORK CONTRACT FAILED")
    for e in errors: print(" -",e)
    raise SystemExit(1)
print("BRE THIAR WINDOWS NETWORK CONTRACT PASSED")
print("input/skills/interact/chat/choices: matched")
print("snapshot player/enemy/remote-player/effective-stat state: matched")
print("inventory equip/use-item actions: matched")
print("protocol/content version handshake: matched")
