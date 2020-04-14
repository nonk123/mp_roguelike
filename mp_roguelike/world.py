class Tile:
    def __init__(self, character="&nbsp;"):
        self.character = character

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []

    def get_tile_at(self, x, y):
        if self.tiles and self.is_in_bounds(x, y):
            return self.tiles[y][x]
        return Tile()

    def is_on_border(self, x, y):
        return x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1

    def is_in_bounds(self, x, y):
        return x >= 0 and y >= 0 and x < width and y < height

    def generate(self):
        self.tiles = []

        for y in range(self.height):
            self.tiles.append([])

            for x in range(self.width):
                character = "#" if self.is_on_border(x, y) else "."
                self.tiles[y].append(Tile(character))
