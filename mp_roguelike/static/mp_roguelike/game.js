const gameElement = document.getElementById("game");
const statusElement = document.getElementById("status");

function render(tiles) {
    gameElement.textContent = "";

    for (row of tiles) {
        const rowElement = document.createElement("tr");

        for (tile of row) {
            const tileElement = document.createElement("td");
            tileElement.class = "tile";
            tileElement.style = `color: ${tile.fg}; background: ${tile.bg};`;
            tileElement.appendChild(document.createTextNode(tile.character));
            rowElement.appendChild(tileElement);
        }

        gameElement.appendChild(rowElement);
    }
}

const handlers = {
    "update": data => render(data),
    "message": data => statusElement.textContent = `${data.sender}: ${data.text}`
};

const socket = new WebSocket(`ws://${window.location.host}/server/`);

function respond(event, data) {
    socket.send(JSON.stringify({
        "e": event,
        "d": data
    }));
}

socket.onopen = function(e) {
    respond("auth", "garbage");
}

socket.onmessage = function(e) {
    const response = JSON.parse(e.data);

    const event = response.e;

    if (event in handlers) {
        handlers[event](response.d);
    }
}
