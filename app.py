from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from game import GameRoom, Player
import uuid

app = Flask(__name__, static_folder="static", template_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# In-memory rooms: room_id -> GameRoom
rooms = {}

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# API via Socket.IO

@socketio.on("create_room")
def handle_create_room(data):
    # data: { "username": str, "max_players": int (<=10) }
    username = data.get("username") or "Player"
    max_players = min(int(data.get("max_players") or 4), 10)
    room_id = str(uuid.uuid4())[:8]
    room = GameRoom(room_id=room_id, max_players=max_players)
    player = Player(sid=request.sid, name=username)
    room.add_player(player)
    rooms[room_id] = room
    join_room(room_id)
    emit("room_created", {"room_id": room_id, "room": room.serializable()}, room=request.sid)
    broadcast_room_update(room)

@socketio.on("join_room")
def handle_join_room(data):
    # data: { "room_id": str, "username": str }
    room_id = data.get("room_id")
    username = data.get("username") or "Player"
    room = rooms.get(room_id)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    if room.is_full():
        emit("error", {"message": "Room full"})
        return
    player = Player(sid=request.sid, name=username)
    room.add_player(player)
    join_room(room_id)
    emit("joined_room", {"room_id": room_id, "room": room.serializable()}, room=request.sid)
    broadcast_room_update(room)

@socketio.on("leave_room")
def handle_leave_room(data):
    room_id = data.get("room_id")
    room = rooms.get(room_id)
    if not room:
        return
    room.remove_player_by_sid(request.sid)
    leave_room(room_id)
    broadcast_room_update(room)

@socketio.on("start_game")
def handle_start_game(data):
    room_id = data.get("room_id")
    room = rooms.get(room_id)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    if room.started:
        emit("error", {"message": "Game already started"})
        return
    room.start_game()
    broadcast_game_state(room)

@socketio.on("add_bot")
def handle_add_bot(data):
    room_id = data.get("room_id")
    name = data.get("name") or "Bot"
    room = rooms.get(room_id)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    if room.is_full():
        emit("error", {"message": "Room full"})
        return
    room.add_bot(name)
    broadcast_room_update(room)

@socketio.on("play_card")
def handle_play_card(data):
    # data: { "room_id": str, "card": { "suit":..., "rank":... } }
    room_id = data.get("room_id")
    card = data.get("card")
    room = rooms.get(room_id)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    player = room.get_player_by_sid(request.sid)
    if not player:
        emit("error", {"message": "Player not in room"})
        return
    ok, msg = room.play_card(player, card)
    if not ok:
        emit("error", {"message": msg}, room=request.sid)
        return
    broadcast_game_state(room)
    # After a play, if next is a bot, let bots play automatically
    room.resolve_bots_turns()
    broadcast_game_state(room)

# Utility emitters
def broadcast_room_update(room):
    socketio.emit("room_update", {"room": room.serializable()}, room=room.room_id)

def broadcast_game_state(room):
    state = room.public_state_for_all()
    socketio.emit("game_state", state, room=room.room_id)
    # send each player's private view (hand)
    for p in room.players:
        private = room.private_state_for_player(p)
        socketio.emit("private_state", private, room=p.sid)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    for room in list(rooms.values()):
        changed = room.remove_player_by_sid(sid)
        if changed:
            broadcast_room_update(room)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)