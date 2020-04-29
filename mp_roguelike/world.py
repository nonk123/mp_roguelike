import random

from .util import color, sign, get_param, Die
from .event import Sender

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
        return isinstance(entity.ai, ControlledAI)

    def attack(self, entity):
        if entity is not None:
            self.move_to(entity.x, entity.y)

class ControlledAI(AI):
    def think(self):
        pass

    def is_enemy(self, entity):
        return not super().is_enemy(entity)

class AggressiveAI(AI):
    def think(self):
        self.attack(self.find_closest_enemy())
        super().think()
        self.entity.turn_done = True

    def is_enemy(self, entity):
        return super().is_enemy(entity) and isinstance(entity.ai, ControlledAI)

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
    def __init__(self, params):
        name = get_param(params, "name", "meh")
        character = get_param(params, "character", "g")
        color = get_param(params, "color", "gray")

        super().__init__(name, character, color)

        self.x = -1
        self.y = -1

        self.view_radius = get_param(params, "view_radius", 8)

        self.hp = get_param(params, "hp_roll", Die(1, 4, +10)).roll()

        self.attacked_by = Tile()

        self.attack_roll = get_param(params, "attack_roll", Die(1, 6))

        ai_args = get_param(params, "ai_args", ())
        self.ai = get_param(params, "ai_type", AggressiveAI)(self, *ai_args)

        self.turn_done = False

        self.added = Sender()
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
        dx, dy = x - self.x, y - self.y

        if dx*dx + dy*dy > self.view_radius**2:
            return False

        cx, cy = self.x, self.y

        if abs(dx) >= abs(dy):
            step = abs(dx);
        else:
            step = abs(dy);

        if step == 0:
            return True

        dx = dx / step;
        dy = dy / step;

        i = 0

        blocked = False

        while i < step:
            cx += dx
            cy += dy
            i += 1

            if self.world.get_tile_at(int(cx), int(cy)).opaque:
                if blocked:
                    return False

                blocked = True

        return True

    def is_in_movement_range(self, dx, dy):
        return abs(dx) <= 1 and abs(dy) <= 1

    def on_add(self, world):
        self.world = world
        self.set_random_position()
        self.added()

    def on_remove(self):
        self.world = None

    def attack(self, entity):
        entity.attacked_by = self
        dmg = self.attack_roll()
        self.attacked(entity, dmg)
        entity.damage(dmg)

    def choose_target(self, targets):
        for target in sorted(targets, key=lambda e: e.hp):
            if self.ai.is_enemy(target):
                return target

    def __move(self, dx, dy, expected_targets):
        new_pos = [self.x + dx, self.y + dy]
        current_targets = self.world.get_entities_at(*new_pos)

        target = self.choose_target(expected_targets)

        if target in current_targets:
            return self.attack(target)

        if not target and not self.world.is_occupied(*new_pos):
            self.x, self.y = new_pos
            return self.moved(dx, dy)

        if target:
            self.target_dodged(target)
            target.dodged()
        elif current_targets:
            self.attack(self.choose_target(current_targets))

    def queue_move(self, dx, dy):
        x, y = self.x + dx, self.y + dy

        if self.is_in_movement_range(dx, dy) and not self.world.is_occupied(x, y):
            expected_targets = self.world.get_entities_at(x, y)
            turn = Turn(self, self.__move, dx, dy, expected_targets)
            self.world.queue_turn(turn)

class SpawnerAI(AI):
    def __init__(self, entity, spawn_fun, max_spawn=5, spawn_cooldown=15):
        super().__init__(entity)

        self.spawn_fun = spawn_fun
        self.max_spawn = max_spawn
        self.spawn_cooldown = spawn_cooldown

        self.spawned = []
        self.turns_since_last_spawn = 0

    def position(self, entity):
        while True:
            entity.x = self.entity.x + random.randint(-1, 1)
            entity.y = self.entity.y + random.randint(-1, 1)

            if not self.entity.world.is_occupied(entity.x, entity.y):
                return

    def think(self):
        if len(self.spawned) < self.max_spawn \
           and self.turns_since_last_spawn >= self.spawn_cooldown:
            entity = self.spawn_fun()

            self.spawned.append(entity)
            entity.added += lambda: self.position(entity)
            entity.dead += lambda: self.spawned.remove(entity)

            self.entity.world.add_entity(entity)

            self.turns_since_last_spawn = 0

        self.turns_since_last_spawn += 1

        self.entity.turn_done = True

class Spawner(Entity):
    def __init__(self, params):
        params["hp_roll"] = Die(5, 20, +300)
        params["attack_roll"] = Die(0, 0)

        params["ai_type"] = SpawnerAI

        spawn_fun = get_param(params, "spawn_fun")
        max_spawn = get_param(params, "max_spawn", 5)
        spawn_cooldown = get_param(params, "spawn_cooldown", 15)

        params["ai_args"] = (spawn_fun, max_spawn, spawn_cooldown)

        super().__init__(params)

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

            other.x += entity.view_radius - entity.x
            other.y += entity.view_radius - entity.y

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

            entity.turn_done = False

        for turn in self.queued_turns:
            turn.do()

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
