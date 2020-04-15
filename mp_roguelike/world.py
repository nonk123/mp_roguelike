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

class Entity(Tile):
    colors = ["red", "green", "blue", "yellow", "orange", "magenta", "cyan"]

    def __init__(self):
        super().__init__(Sprite("@", random.choice(self.colors)))

        self.x = -1
        self.y = -1

    def remove(self):
        self.world.remove_entity(self)

    def random_position(self):
        while self.world.is_occupied(self.x, self.y):
            self.x = random.randint(0, self.world.width)
            self.y = random.randint(0, self.world.height)

    def is_at(self, x, y):
        return self.x == x and self.y == y

    def on_add(self, world):
        self.world = world
        self.random_position()

    def on_remove(self):
        self.world = None

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []
        self.entities = []

    def get_tile_at(self, x, y):
        if self.is_in_bounds(x, y):
            return self.tiles[y][x]
        return Tile()

    def get_entities_at(self, x, y):
        if self.is_in_bounds(x, y):
            return [entity for entity in self.entities if entity.is_at(x, y)]
        return []

    def is_on_border(self, x, y):
        return x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1

    def is_in_bounds(self, x, y):
        return x >= 0 and y >= 0 and x < self.width and y < self.height

    def is_occupied(self, x, y):
        return not self.is_in_bounds(x, y) or self.get_tile_at(x, y).impassable

    def add_entity(self, entity):
        entity.on_add(self)
        self.entities.append(entity)

    def remove_entity(self, entity):
        entity.on_remove()
        self.entities.remove(entity)

    def get_sprites(self):
        sprites = []

        for y, row in enumerate(self.tiles):
            sprites.append([])

            for x, tile in enumerate(row):
                sprites[y].append(tile.sprite)

                for entity in self.get_entities_at(x, y):
                    sprites[y][x] = entity.sprite

        return sprites

    def generate(self):
        self.tiles = []

        for y in range(self.height):
            self.tiles.append([])

            for x in range(self.width):
                tile = Wall() if self.is_on_border(x, y) else Floor()
                self.tiles[y].append(tile)
