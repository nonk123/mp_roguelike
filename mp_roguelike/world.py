import random

from .event import Sender
from .util import Die

from .tiles import Tile, Floor, Wall
from .entities import Entity, Spawner

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []
        self.entities = []
        self.queued_turns = []

        self.updated = Sender()
        self.entity_died = Sender()

    def get_tile_at(self, x, y):
        return self.tiles[y][x] if self.is_in_bounds(x, y) else Tile()

    def set_tile(self, x, y, tile):
        if self.is_in_bounds(x, y):
            self.tiles[y][x] = tile

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

    def get_visible_entities(self, around):
        visible = []

        for other in self.entities:
            if around.can_see(other.x, other.y):
                visible.append(other)

        return visible

    def get_renderable(self, entity):
        tiles = []

        for y in range(-entity.view_radius, entity.view_radius + 1):
            y += entity.y

            row = []

            for x in range(-entity.view_radius, entity.view_radius + 1):
                x += entity.x

                if entity.can_see(x, y):
                    tile = self.get_tile_at(x, y)

                    if isinstance(tile, Wall):
                        tile = {
                            **tile.__dict__,
                            "character": tile.get_fancy_character(self, x, y)
                        }

                    row.append(tile)
                else:
                    row.append(Tile())

            tiles.append(row)

        entities = entity.get_visible_entities()

        for i, other in enumerate(entities):
            other = other.stripped()

            other["x"] += entity.view_radius - entity.x
            other["y"] += entity.view_radius - entity.y

            entities[i] = other

        return tiles, entities

    def queue_turn(self, turn):
        if not turn.entity.turn_done:
            self.queued_turns.append(turn)
        turn.entity.turn_done = True

    def update(self):
        for entity in self.entities:
            entity.ai.think()

        for entity in self.entities:
            if not entity.turn_done:
                return

        for turn in self.queued_turns:
            turn.do()
            turn.entity.turn_done = False

        self.queued_turns = []

        self.updated()

    def __count_walls(self, x, y):
        to_check = [
            (x - 1, y - 1),
            (x, y - 1),
            (x + 1, y - 1),
            (x - 1, y),
            (x, y),
            (x + 1, y),
            (x - 1, y + 1),
            (x, y + 1),
            (x + 1, y + 1)
        ]

        walls_count = 0

        for coords in to_check:
            if isinstance(self.get_tile_at(*coords), Wall):
                walls_count += 1

        return walls_count

    def __run_cellular_automata(self):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                if self.__count_walls(x, y) > 5:
                    self.set_tile(x, y, Wall(self.fg, self.bg))

    def generate(self):
        self.tiles = []

        self.fg, self.bg = random.choice([
            ("gray", "#303030")
        ])

        for y in range(self.height):
            self.tiles.append([])

            for x in range(self.width):
                if self.is_on_border(x, y) or random.random() <= 0.4:
                    tile = Wall(self.fg, self.bg)
                else:
                    tile = Floor(self.bg)

                self.tiles[y].append(tile)

        for i in range(4):
            self.__run_cellular_automata()

        def spawn_goblin():
            return Entity({
                "name": "Goblin",
                "character": "g",
                "color": "darkgreen",
                "hp_roll": Die(1, 3, +4),
                "attack_roll": Die(1, 4, -1),
                "view_radius": 6
            })

        for i in range(20):
            self.add_entity(Spawner({
                "name": "Goblin Spawner",
                "character": "*",
                "color": "brown",
                "spawn_fun": spawn_goblin
            }))

world = World(100, 100)
world.generate()
world.update()
