import random

from .util import color, sign, Die
from .event import Sender

class Tile:
    def __init__(self, name="thin air", character=" ", color="gray", background="black"):
        self.name = name
        self.character = character
        self.background = background
        self.color = color
        self.impassable = False

    @property
    def fancy_name(self):
        return color(self.color, self.name)

    @property
    def fancy_you(self):
        return color(self.color, "You")

class Floor(Tile):
    characters = (".", ".", ".", ",")

    def __init__(self, background="gray"):
        super().__init__(f"{color} floor", random.choice(self.characters), "gray", background)

class Wall(Tile):
    def __init__(self, color="gray"):
        super().__init__(f"{color} wall", "#", "black", color)

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

class AI:
    def __init__(self, entity):
        self.entity = entity
        self.queued_path = []

    @property
    def can_think(self):
        return True

    def think(self):
        if self.queued_path:
            x, y = self.queued_path.pop(0)
            self.move(x - self.entity.x, y - self.entity.y)

    def move(self, dx, dy):
        self.entity.queue_move(dx, dy)

    def move_to(self, x, y):
        self.queued_path = []

        at = [self.entity.x, self.entity.y]

        while at != [x, y]:
            at[0] += sign(x - at[0])
            at[1] += sign(y - at[1])

            self.queued_path.append((*at,))

    def is_enemy(self, entity):
        # TODO: smarter check.
        return not entity.is_at(self.entity.x, self.entity.y)

    def attack(self, entity):
        if entity is not None:
            self.move_to(entity.x, entity.y)

class DummyAI(AI):
    @property
    def can_think(self):
        return False

class AggressiveAI(AI):
    def think(self):
        self.attack(self.find_closest_enemy())
        super().think()
        self.entity.turn_done = True

    def find_closest_enemy(self):
        closest = None

        for entity in self.entity.get_visible_entities():
            if closest is None:
                ddist = -10
            else:
                ddist = entity.dist(self.entity) - closest.dist(self.entity)

            if self.is_enemy(entity) and ddist < 0:
                closest = entity

        return closest

class Entity(Tile):
    colors = ["red", "green", "blue", "yellow", "orange", "magenta", "cyan"]

    attack_rolls = [Die(1, 6, +3), Die(2, 4, +2), Die(3, 4), Die(2, 6, +1)]

    def __init__(self, name, ai_type=AI):
        super().__init__(name, "@", random.choice(self.colors))

        self.x = -1
        self.y = -1

        self.view_radius = 8

        self.hp = Die(2, 4, +20).roll()

        self.attacked_by = Tile()
        self.attack_roll = random.choice(self.attack_rolls)

        self.ai = ai_type(self)

        self.turn_done = False

        self.damaged = Sender()
        self.dead = Sender()
        self.attacked = Sender()
        self.moved = Sender()
        self.dodged = Sender()
        self.target_dodged = Sender()

    def remove(self):
        self.world.remove_entity(self)

    def dist(self, other):
        dx = other.x - self.x
        dy = other.y - self.y

        return dx*dx + dy*dy

    def stripped(self):
        tile = Tile(self.name, self.character, self.color)

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

    def get_visible_entities(self):
        if self.world:
            return self.world.get_visible_entities(self)
        else:
            return []

    def get_renderable(self):
        if self.world:
            return self.world.get_renderable(self)
        else:
            return [], []

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
        self.world.entity_died(self)
        self.dead()
        self.remove()

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
        x, y = self.x + dx, self.y + dy

        if self.is_in_movement_range(dx, dy) and not self.world.is_occupied(x, y):
            expected_targets = self.world.get_entities_at(x, y)
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
        self.entity_died = Sender()

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
                    row.append(self.get_tile_at(x, y))
                else:
                    row.append(Tile())

            tiles.append(row)

        entities = entity.get_visible_entities()

        for i, other in enumerate(entities):
            other = other.stripped()

            other.x += entity.view_radius - entity.x
            other.y += entity.view_radius - entity.y

            entities[i] = other

        return tiles, entities

    def queue_turn(self, turn):
        if not turn.entity.turn_done:
            self.queued_turns.append(turn)
        turn.entity.turn_done = True

    def update(self):
        while len(self.entities) < 5:
            self.add_entity(Entity("Gebastel", AggressiveAI))

        for entity in self.entities:
            if not entity.ai.can_think and not entity.turn_done:
                return

            entity.ai.think()

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
