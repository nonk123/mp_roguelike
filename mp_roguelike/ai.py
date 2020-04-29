import random

from .util import sign

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
