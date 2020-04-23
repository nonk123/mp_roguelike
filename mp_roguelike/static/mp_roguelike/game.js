const gameElement = document.getElementById("game");
const statusElement = document.getElementById("status");

function getTileStyle(tile) {
    return `\
color: ${tile.color};
background: black;
font-size: 15px;`;
}

function draw(data) {
    const display = data.tiles;

    for (const entity of data.entities) {
        display[entity.y][entity.x] = entity;
    }

    gameElement.textContent = "";

    for (const row of display) {
        const rowElement = document.createElement("tr");

        for (const tile of row) {
            const dataElement = document.createElement("td");

            const tileElement = document.createElement("span");
            tileElement.style = getTileStyle(tile);
            tileElement.textContent = tile.character;
            dataElement.appendChild(tileElement);

            rowElement.appendChild(dataElement);
        }

        gameElement.appendChild(rowElement);
    }
}

function displayMessage(data) {
    const messageElement = document.createElement("span");
    messageElement.innerHTML = `${data.sender}: ${data.text}<br>`;

    statusElement.appendChild(messageElement);
    statusElement.scrollTop = statusElement.scrollHeight;
}

const handlers = {
    "update": draw,
    "message": displayMessage
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
        "turn_type": type,
        "data": data
    });
}

socket.onopen = function(e) {
    respond("auth", {
        "name": document.getElementById("name").value
    });
}

socket.onclose = function(e) {
    displayMessage({"sender": e.code, text: "disconnected"});
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
        "dx": dx,
        "dy": dy
    });
}

const inputField = document.getElementById("chatInput");

inputField.addEventListener("keydown", event => {
    if (event.key == "Enter") {
        respond("chat", {
            "message": inputField.value
        });

        inputField.value = "";
    }

    if (event.key == "Escape") {
        inputField.blur();
    }
});

const keys = {
    "t": () => inputField.focus()
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

gameElement.focus();
