import random

class Sprite:
    def __init__(self, character="&nbsp;", fg="gray", bg="black"):
        self.character = character
        self.fg = fg
        self.bg = bg

class Tile:
    def __init__(self, sprite=Sprite()):
        self.sprite = sprite
        self.impassable = False

class Floor(Tile):
    characters = (".", ".", ".", ",")

    def __init__(self, color="green"):
        super().__init__(Sprite(random.choice(Floor.characters), color))

class Wall(Tile):
    def __init__(self, color="saddlebrown"):
        super().__init__(Sprite("#", color))

        self.impassable = True

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

    def get_sprites(self):
        sprites = []

        for y, row in enumerate(self.tiles):
            sprites.append([])

            for tile in row:
                sprites[y].append(tile.sprite)

        return sprites

    def generate(self):
        self.tiles = []

        for y in range(self.height):
            self.tiles.append([])

            for x in range(self.width):
                tile = Wall() if self.is_on_border(x, y) else Floor()
                self.tiles[y].append(tile)
