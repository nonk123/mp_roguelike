const gameElement = document.getElementById("game");

function render(tiles) {
    gameElement.textContent = "";

    for (row of tiles) {
        const rowElement = document.createElement("tr");

        for (tile of row) {
            const tileElement = document.createElement("td");
            tileElement.class = "tile";
            tileElement.appendChild(document.createTextNode(tile.character));
            rowElement.appendChild(tileElement);
        }

        gameElement.appendChild(rowElement);
    }
}

const socket = new WebSocket(`ws://${window.location.host}/server/`);

socket.onmessage = function(e) {
    render(JSON.parse(e.data));
}
