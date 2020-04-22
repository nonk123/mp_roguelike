import random

from .util import color, Die
from .event import Sender

class Sprite:
    def __init__(self, character="\u00a0", fg="gray", bg="black"):
        self.character = character
        self.fg = fg
        self.bg = bg

class Tile:
    def __init__(self, name="thin air", sprite=Sprite()):
        self.name = name
        self.sprite = sprite
        self.impassable = False

    @property
    def fancy_name(self):
        return color(self.sprite.fg, self.name)

    @property
    def fancy_you(self):
        return color(self.sprite.fg, "You")

class Floor(Tile):
    characters = (".", ".", ".", ",")

    def __init__(self, color="gray"):
        sprite = Sprite(random.choice(Floor.characters), color)

        super().__init__(f"{color} floor", sprite)

class Wall(Tile):
    def __init__(self, color="gray"):
        super().__init__(f"{color} wall", Sprite("#", color))

        self.impassable = True

class Turn:
    def __init__(self, entity, action, *args, **kwargs):
        self.entity = entity
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def do(self):
        if self.entity.world:
            self.action(*self.args, **self.kwargs)

class Entity(Tile):
    colors = ["red", "green", "blue", "yellow", "orange", "magenta", "cyan"]
    attack_rolls = [Die(1, 6, +3), Die(2, 4, +2), Die(3, 4), Die(2, 6, +1)]

    def __init__(self, name):
        super().__init__(name, Sprite("@", random.choice(self.colors)))

        self.x = -1
        self.y = -1

        self.view_radius = 8

        self.hp = Die(2, 4, +20).roll()

        self.attacked_by = Tile()
        self.attack_roll = random.choice(self.attack_rolls)

        self.turn_done = False

        self.damaged = Sender()
        self.dead = Sender()
        self.attacked = Sender()
        self.moved = Sender()
        self.dodged = Sender()
        self.target_dodged = Sender()

    def remove(self):
        self.world.remove_entity(self)

    def stripped(self):
        tile = Tile(self.name, self.sprite)

        extras = {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "view_radius": self.view_radius,
            "attack_roll": self.attack_roll
        }

        for k, v in extras.items():
            setattr(tile, k, v)

        return tile

    def set_random_position(self):
        while self.world.is_occupied(self.x, self.y):
            self.x = random.randint(0, self.world.width)
            self.y = random.randint(0, self.world.height)

    def damage(self, dmg):
        self.hp -= dmg

        self.damaged(dmg)

        if self.hp <= 0 and self.hp + dmg > 0:
            self.die()

    def die(self):
        self.remove()
        self.dead()

    def is_at(self, x, y):
        return self.x == x and self.y == y

    def can_see(self, x, y):
        dx = self.x - x
        dy = self.y - y

        return dx*dx + dy*dy <= self.view_radius * self.view_radius

    def is_in_movement_range(self, dx, dy):
        return abs(dx) <= 1 and abs(dy) <= 1

    def on_add(self, world):
        self.world = world
        self.set_random_position()

    def on_remove(self):
        self.world = None

    def attack(self, entity):
        entity.attacked_by = self
        dmg = self.attack_roll()
        self.attacked(entity, dmg)
        entity.damage(dmg)

    def choose_target(self, targets):
        return targets[0] if targets else None

    def __move(self, dx, dy, expected_targets):
        new_pos = [self.x + dx, self.y + dy]
        current_targets = self.world.get_entities_at(*new_pos)

        target = self.choose_target(expected_targets)

        # No suicide allowed.
        if target is self:
            return

        # The target is still in range, strike it.
        if target in current_targets:
            return self.attack(target)

        if target:
            # The target has moved out of range; attacked failed.
            self.target_dodged(target)
            target.dodged()
        elif current_targets:
            # Another enemy has moved into range, so it receives a beating.
            self.attack(self.choose_target(current_targets))
        elif not current_targets and not self.world.is_occupied(*new_pos):
            # Space clear, move into it.
            self.x, self.y = new_pos
            self.moved(dx, dy)

    def queue_move(self, dx, dy):
        if self.is_in_movement_range(dx, dy):
            expected_targets = self.world.get_entities_at(self.x + dx, self.y + dy)
            turn = Turn(self, self.__move, dx, dy, expected_targets)
            self.world.queue_turn(turn)

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []
        self.entities = []
        self.queued_turns = []

        self.updated = Sender()

    def get_tile_at(self, x, y):
        return self.tiles[y][x] if self.is_in_bounds(x, y) else Tile()

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

    def get_sprite_at(self, x, y):
        sprite = self.get_tile_at(x, y).sprite

        for entity in self.get_entities_at(x, y):
            sprite = entity.sprite

        return sprite

    def get_visible(self, entity):
        tiles = []

        for y in range(-entity.view_radius, entity.view_radius + 1):
            y += entity.y

            row = []

            for x in range(-entity.view_radius, entity.view_radius + 1):
                x += entity.x

                if entity.can_see(x, y):
                    row.append(self.get_tile_at(x, y))
                else:
                    row.append(Tile())

            tiles.append(row)

        entities = []

        for other in self.entities:
            if entity.can_see(other.x, other.y):
                other = other.stripped()

                other.x += entity.view_radius - entity.x
                other.y += entity.view_radius - entity.y

                entities.append(other)

        return tiles, entities

    def queue_turn(self, turn):
        if not turn.entity.turn_done:
            self.queued_turns.append(turn)
        turn.entity.turn_done = True

    def update(self):
        if False in [entity.turn_done for entity in self.entities]:
            return

        for turn in self.queued_turns:
            turn.do()

        for entity in self.entities:
            entity.turn_done = False

        self.queued_turns = []

        self.updated()

    def generate(self):
        self.tiles = []

        for y in range(self.height):
            self.tiles.append([])

            for x in range(self.width):
                tile = Wall() if self.is_on_border(x, y) else Floor()
                self.tiles[y].append(tile)
