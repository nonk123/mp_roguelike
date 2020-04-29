from .util import color

class Tile:
    def __init__(self, name="thin air", character=" ", color="gray", background="black"):
        self.name = name
        self.character = character
        self.background = background
        self.color = color

    @property
    def fancy_name(self):
        return color(self.color, self.name)

    @property
    def fancy_you(self):
        return color(self.color, "You")

    @property
    def impassable(self):
        return False

    @property
    def opaque(self):
        return False

class Floor(Tile):
    def __init__(self, color):
        super().__init__(f"{color} floor", " ", "gray", color)

class Wall(Tile):
    def __init__(self, color, background):
        super().__init__(f"{color} wall", "#", color, background)

    @property
    def impassable(self):
        return True

    @property
    def opaque(self):
        return True

    def get_fancy_character(self, world, x, y):
        wall_characters = {
            "0,0,0,0": "○",
            "1,0,0,0": "○",
            "0,1,0,0": "○",
            "1,1,0,0": "═",
            "0,0,1,0": "○",
            "0,0,0,1": "○",
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
        }

        positions = [
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1)
        ]

        adjacent = []

        for pos in positions:
            if world.get_tile_at(*pos).impassable:
                adjacent.append("1")
            else:
                adjacent.append("0")

        return wall_characters[",".join(adjacent)]
