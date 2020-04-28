const gameElement = document.getElementById("game");
const statusElement = document.getElementById("status");

display = [];

function draw(data) {
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

            function isWall(x, y) {
                if (x >= 0 && x < display[0].length && y >= 0 && y < display.length) {
                    return display[y][x].character == "#";
                } else {
                    return false;
                }
            }

            let character = tile.character;

            if (isWall(x, y)) {
                const aroundPositions = [
                    [x - 1, y],
                    [x + 1, y],
                    [x, y - 1],
                    [x, y + 1]
                ];

                const wallsAround = [];

                for (const pos of aroundPositions) {
                    wallsAround.push(0 + isWall(...pos));
                }

                const wallCharacters = {
                    "0,0,0,0": "○",
                    "1,0,0,0": "═",
                    "0,1,0,0": "═",
                    "1,1,0,0": "═",
                    "0,0,1,0": "║",
                    "0,0,0,1": "║",
                    "0,0,1,1": "║",
                    "1,0,1,0": "╝",
                    "1,0,0,1": "╗",
                    "0,1,1,0": "╚",
                    "0,1,0,1": "╔",
                    "1,0,1,1": "╣",
                    "0,1,1,1": "╠",
                    "1,1,1,0": "╩",
                    "1,1,0,1": "╦",
                    "1,1,1,1": "╬"
                };

                character = wallCharacters[wallsAround.join(",")];
            }

            if (tile.character && tile.character != " ") {
                ctx.fillStyle = tile.color;
                ctx.fillText(character, dx, dy);
            }
        }
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
