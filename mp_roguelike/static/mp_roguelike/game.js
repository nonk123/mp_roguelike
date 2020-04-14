const gameElement = document.getElementById("game");

class Tile {
    constructor(character) {
        this.character = character;
    }

    get character() {
        return this._character;
    }

    set character(character) {
        this._character = character;
    }
}

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

const tiles = [];

const w = 50;
const h = 50;

for (let y = 0; y < h; y++) {
    tiles[y] = [];

    for (let x = 0; x < w; x++) {
        if (x == 0 || y == 0 || x == w - 1 || y == h - 1) {
            tiles[y][x] = new Tile("#");
        } else {
            tiles[y][x] = new Tile(".");
        }
    }
}

render(tiles);
