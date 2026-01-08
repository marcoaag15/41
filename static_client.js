const socket = io();

let currentRoom = null;
let myName = null;
let mySid = null;

// UI refs
const createRoomBtn = document.getElementById("createRoomBtn");
const joinRoomBtn = document.getElementById("joinRoomBtn");
const usernameInput = document.getElementById("username");
const roomIdInput = document.getElementById("roomIdInput");
const lobbyDiv = document.getElementById("lobby");
const roomIdSpan = document.getElementById("roomId");
const playersList = document.getElementById("playersList");
const maxPlayersInput = document.getElementById("maxPlayers");
const addBotBtn = document.getElementById("addBotBtn");
const startGameBtn = document.getElementById("startGameBtn");
const gameDiv = document.getElementById("game");
const handDiv = document.getElementById("hand");
const publicStateDiv = document.getElementById("publicState");
const logDiv = document.getElementById("log");
const turnInfo = document.getElementById("turnInfo");
const leaveBtn = document.getElementById("leaveBtn");

createRoomBtn.onclick = () => {
  myName = usernameInput.value || "Player";
  const max_players = parseInt(maxPlayersInput.value) || 4;
  socket.emit("create_room", { username: myName, max_players });
};

joinRoomBtn.onclick = () => {
  myName = usernameInput.value || "Player";
  const roomId = roomIdInput.value.trim();
  if (!roomId) { alert("Introduce room id"); return; }
  socket.emit("join_room", { room_id: roomId, username: myName });
};

addBotBtn.onclick = () => {
  socket.emit("add_bot", { room_id: currentRoom });
};

startGameBtn.onclick = () => {
  socket.emit("start_game", { room_id: currentRoom });
};

leaveBtn.onclick = () => {
  socket.emit("leave_room", { room_id: currentRoom });
  lobbyDiv.style.display = "none";
  gameDiv.style.display = "none";
};

socket.on("connect", () => {
  mySid = socket.id;
});

socket.on("room_created", (data) => {
  currentRoom = data.room_id;
  roomIdSpan.textContent = currentRoom;
  lobbyDiv.style.display = "block";
  updatePlayers(data.room.players);
});

socket.on("joined_room", (data) => {
  currentRoom = data.room_id;
  roomIdSpan.textContent = currentRoom;
  lobbyDiv.style.display = "block";
  updatePlayers(data.room.players);
});

socket.on("room_update", (data) => {
  const room = data.room;
  currentRoom = room.room_id;
  roomIdSpan.textContent = currentRoom;
  updatePlayers(room.players);
});

socket.on("game_state", (state) => {
  lobbyDiv.style.display = "none";
  gameDiv.style.display = "block";
  publicStateDiv.textContent = JSON.stringify(state, null, 2);
  turnInfo.textContent = `Turn index: ${state.turn_index}`;
  appendLog("Game state updated.");
});

socket.on("private_state", (payload) => {
  // payload: { you: { hand: [...] }, public: {...} }
  const you = payload.you;
  renderHand(you.hand);
});

socket.on("error", (d) => {
  alert("Error: " + (d.message || JSON.stringify(d)));
});

function updatePlayers(players) {
  playersList.innerHTML = "";
  players.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.name} ${p.is_bot ? "(bot)" : ""} — cartas en mano: ${p.cards_in_hand}`;
    playersList.appendChild(li);
  });
}

function renderHand(hand) {
  handDiv.innerHTML = "";
  hand.forEach(c => {
    const cardEl = document.createElement("div");
    cardEl.className = "card";
    cardEl.textContent = `${c.rank} de ${c.suit}`;
    const btn = document.createElement("button");
    btn.textContent = "Jugar";
    btn.onclick = () => playCard(c);
    cardEl.appendChild(document.createElement("br"));
    cardEl.appendChild(btn);
    handDiv.appendChild(cardEl);
  });
}

function playCard(card) {
  socket.emit("play_card", { room_id: currentRoom, card });
  appendLog(`Jugaste: ${card.rank} de ${card.suit}`);
}

function appendLog(msg) {
  const p = document.createElement("div");
  p.textContent = msg;
  logDiv.prepend(p);
}