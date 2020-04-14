class Tile:
    def __init__(self, character="&nbsp;"):
        self.character = character

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def getTileAt(self, x, y):
        if self.tiles and self.tiles[y]:
            return self.tiles[y][x]
        return Tile()

    def isOnBorder(self, x, y):
        return x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1

    def isInBounds(self, x, y):
        return x >= 0 and y >= 0 and x < width and y < height

    def generate(self):
        self.tiles = []

        for y in range(self.height):
            self.tiles.append([])

            for x in range(self.width):
                character = "#" if self.isOnBorder(x, y) else "."
                self.tiles[y].append(Tile(character))
