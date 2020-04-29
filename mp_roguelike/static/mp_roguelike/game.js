const display = [];

function draw(data) {
    const gameElement = document.getElementById("game");

    if (data && data.tiles && data.entities) {
        for (const [y, row] of data.tiles.entries()) {
            display[y] = row.slice();
        }

        for (const entity of data.entities) {
            display[entity.y][entity.x] = {
                character: entity.character,
                color: entity.color,
                background: display[entity.y][entity.x].background
            };
        }
    }

    gameElement.width = gameElement.clientWidth;
    gameElement.height = gameElement.clientHeight;

    const ctx = gameElement.getContext("2d");

    const h = Math.floor(gameElement.height / display.length);
    ctx.font = `${h}px monospace`;

    const w = Math.ceil(ctx.measureText("@").width);

    ctx.textBaseline = "top";

    for (const [y, row] of display.entries()) {
        for (const [x, tile] of row.entries()) {
            const [dx, dy] = [x * w, y * h];

            if (tile.background) {
                ctx.fillStyle = tile.background;
                ctx.fillRect(dx, dy, w, h);
            }

            if (tile.character && tile.character != " ") {
                ctx.fillStyle = tile.color;
                ctx.fillText(tile.character, dx, dy);
            }
        }
    }
}

function dieToString(die) {
    return `${die.count}d${die.sides}${die.inc < 0 ? "-" : "+"}${die.inc}`
}

function update(data) {
    const statusElement = document.getElementById("status");
    statusElement.textContent = "";

    const characterElement = document.createElement("div");
    characterElement.style.fontSize = "20px";
    characterElement.style.color = data.player.color;
    characterElement.textContent = data.player.character;

    statusElement.appendChild(characterElement);

    const hpElement = document.createElement("div");
    hpElement.style.fontSize = "13px";
    hpElement.style.marginTop = "7px";
    hpElement.textContent = `Health: ${data.player.hp}`;

    statusElement.appendChild(hpElement);

    const attackElement = document.createElement("div");
    attackElement.style.fontSize = "13px";
    attackElement.textContent = `Attack: ${dieToString(data.player.attack_roll)}`;

    statusElement.appendChild(attackElement);

    const turnIndicator = document.createElement("div");
    turnIndicator.style.fontSize = "10px";
    turnIndicator.textContent = `Waiting for ${data.player.turn_done ? "others" : "you"}`

    statusElement.appendChild(turnIndicator);

    draw(data);
}

window.onresize = function(e) { draw() };

function displayMessage(data) {
    const messagesElement = document.getElementById("messages");

    const message = document.createElement("span");
    message.innerHTML = `${data.sender}: ${data.text}<br>`;

    messagesElement.appendChild(message);
    messagesElement.scrollTop = messagesElement.scrollHeight;
}

const handlers = {
    update: update,
    message: displayMessage
};

const socket = new WebSocket(`ws://${window.location.host}/server/`);

function respond(event, data="") {
    socket.send(JSON.stringify({
        "e": event,
        "d": data
    }));
}

function turn(type, data) {
    respond("turn", {
        turn_type: type,
        data: data
    });
}

socket.onopen = function(e) {
    respond("auth", {
        name: document.getElementById("name").value
    });
}

socket.onclose = function(e) {
    displayMessage({sender: e.code, text: "disconnected"});
}

socket.onmessage = function(e) {
    const response = JSON.parse(e.data);

    const event = response.e;

    if (event in handlers) {
        handlers[event](response.d);
    }
}

function move(dx, dy) {
    turn("move", {
        dx: dx,
        dy: dy
    });
}

const inputField = document.getElementById("chatInput");

inputField.addEventListener("keydown", event => {
    if (event.key == "Enter") {
        respond("chat", {
            message: inputField.value
        });

        inputField.value = "";
    }

    if (event.key == "Escape") {
        inputField.blur();
    }
});

const keys = {
    t: () => inputField.focus()
};

const gameKeys = {
    "1,b": () => move(-1, 1),
    "2,j": () => move(0, 1),
    "3,n": () => move(1, 1),
    "4,h": () => move(-1, 0),
    "5,.": () => move(0, 0),
    "6,l": () => move(1, 0),
    "7,y": () => move(-1, -1),
    "8,k": () => move(0, -1),
    "9,u": () => move(1, -1)
};

function keyIn(key, bindings) {
    for (binding of bindings.split(",")) {
        if (key === binding) {
            return true;
        }
    }

    return false;
}

function onKeyPress(key, keys) {
    for (const bindings in keys) {
        if (keyIn(key, bindings)) {
            keys[bindings]();
            return true;
        }
    }

    return false;
}

document.addEventListener("keyup", event => {
    const key = event.key;

    if (chatInput == document.activeElement || !onKeyPress(key, gameKeys)) {
        onKeyPress(key, keys);
    }
});
