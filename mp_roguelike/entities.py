import random

from .event import Sender
from .util import get_param, Die

from .tiles import Tile
from . import ai

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
        self.ai = get_param(params, "ai_type", ai.AggressiveAI)(self, *ai_args)

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
        return {
            **Tile(self.name, self.character, self.color).__dict__,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "view_radius": self.view_radius,
            "attack_roll": self.attack_roll,
            "turn_done": self.turn_done
        }

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

class Spawner(Entity):
    def __init__(self, params):
        params["hp_roll"] = Die(5, 20, +300)
        params["attack_roll"] = Die(0, 0)

        params["ai_type"] = ai.SpawnerAI

        spawn_fun = get_param(params, "spawn_fun")
        max_spawn = get_param(params, "max_spawn", 5)
        spawn_cooldown = get_param(params, "spawn_cooldown", 15)

        params["ai_args"] = (spawn_fun, max_spawn, spawn_cooldown)

        super().__init__(params)
