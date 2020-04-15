const gameElement = document.getElementById("game");
const statusElement = document.getElementById("status");

let display = [];

function draw() {
    gameElement.textContent = "";

    for (row of display) {
        const rowElement = document.createElement("tr");

        for (sprite of row) {
            const spriteElement = document.createElement("td");
            spriteElement.class = "tile";
            spriteElement.style = `color: ${sprite.fg}; background: ${sprite.bg};`;
            spriteElement.appendChild(document.createTextNode(sprite.character));
            rowElement.appendChild(spriteElement);
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

socket.onmessage = function(e) {
    const response = JSON.parse(e.data);

    const event = response.e;

    if (event in handlers) {
        handlers[event](response.d);
    }
}

document.addEventListener("keydown", function(event) {
    const key = event.key;

    const movement = {
        "1": [-1,  1],
        "2": [ 0,  1],
        "3": [ 1,  1],
        "4": [-1,  0],
        "6": [ 1,  0],
        "7": [-1, -1],
        "8": [ 0, -1],
        "9": [ 1, -1]
    }

    if (key in movement) {
        respond("move", {
            "dx": movement[key][0],
            "dy": movement[key][1]
        });
    }
});
