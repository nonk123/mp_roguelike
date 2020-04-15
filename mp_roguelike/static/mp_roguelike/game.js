const gameElement = document.getElementById("game");
const statusElement = document.getElementById("status");

let display = [];

function draw() {
    gameElement.textContent = "";

    for (row of display) {
        const rowElement = document.createElement("tr");

        for (sprite of row) {
            const style = `\
color: ${sprite.fg};
background: ${sprite.bg};
font-size: 15px;`;

            const dataElement = document.createElement("td");

            const spriteElement = document.createElement("span");
            spriteElement.style = style;
            spriteElement.textContent = sprite.character;

            dataElement.appendChild(spriteElement);
            rowElement.appendChild(dataElement);
        }

        gameElement.appendChild(rowElement);
    }
}

function updateDisplay(sprites) {
    if (Array.isArray(sprites)) {
        for (y in sprites) {
            const row = sprites[y];

            display[y] = [];

            for (x in row) {
                display[y][x] = row[x];
            }
        }
    } else {
        for (pos in sprites) {
            const x = pos.split(":")[0];
            const y = pos.split(":")[1];

            display[y][x] = sprites[pos];
        }
    }

    draw();
}

function displayMessage(data) {
    const messageElement = document.createElement("span");
    messageElement.innerHTML = `${data.sender}: ${data.text}<br>`;

    statusElement.appendChild(messageElement);
    statusElement.scrollTop = statusElement.scrollHeight;
}

const handlers = {
    "update": updateDisplay,
    "delta": updateDisplay,
    "message": displayMessage
};

const socket = new WebSocket(`ws://${window.location.host}/server/`);

function respond(event, data="") {
    socket.send(JSON.stringify({
        "e": event,
        "d": data
    }));
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
    respond("move", {
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
})

const keys = {
    "t": () => inputField.focus()
}

const gameKeys = {
    "1": () => move(-1, 1),
    "2": () => move(0, 1),
    "3": () => move(1, 1),
    "4": () => move(-1, 0),
    "6": () => move(1, 0),
    "7": () => move(-1, -1),
    "8": () => move(0, -1),
    "9": () => move(1, -1),
}

function onKeyPress(key, keys) {
    if (key in keys) {
        keys[key]();
        return true;
    }

    return false;
}

document.addEventListener("keyup", event => {
    const key = event.key;

    if (chatInput.hasFocus || !onKeyPress(key, gameKeys)) {
        onKeyPress(key, keys);
    }
});

gameElement.focus();
