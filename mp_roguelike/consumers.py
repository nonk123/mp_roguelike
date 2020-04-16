import jsonpickle

from channels.generic.websocket import WebsocketConsumer

import random

from .world import World, Entity

world = World(20, 20)
world.generate()

players = []

class Player:
    def __init__(self, consumer, name):
        self.consumer = consumer
        self.__name = name
        self.respawn()

    def __delta_all(self, dx, dy):
        self.consumer.all(self.consumer.delta)

    def show_death_message(self):
        msg = f"{self.get_fancy_name()} was killed by {self.entity.attacked_by.get_fancy_name()}"
        self.consumer.send_message_to_all("Game", msg)

    def show_dealt_damage(self, enemy, dmg):
        msg = f"You hit {enemy.get_fancy_name()} for {dmg} damage!"
        self.consumer.send_message("Game", msg)

    def show_taken_damage(self, dmg):
        msg = f"{self.entity.attacked_by.get_fancy_name()} hit you for {dmg} damage!"
        self.consumer.send_message("Game", msg)

    def respawn(self):
        self.entity = Entity(self.__name)
        world.add_entity(self.entity)
        self.consumer.send_message("Game", f"You have {self.entity.hp} HP.")

        self.entity.moved += self.__delta_all
        self.entity.dead += self.show_death_message
        self.entity.dead += self.respawn
        self.entity.damaged += self.show_taken_damage
        self.entity.attacked += self.show_dealt_damage

    def get_fancy_name(self):
        return self.entity.get_fancy_name()

    def on_remove(self):
        self.entity.remove()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.handlers = {
            "auth": self.on_auth,
            "move": self.on_move,
            "chat": self.on_chat
        }

        self.accept();

    def disconnect(self, close_code):
        if hasattr(self, "player") and self.player:
            goodbye_msg = f"{self.player.get_fancy_name()} disconnected"
            self.send_message_to_all("Server", goodbye_msg)

            self.player.on_remove()
            players.remove(self.player)

            self.all(self.delta)

    def receive(self, text_data):
        decoded = jsonpickle.decode(text_data)

        event = decoded["e"]

        if event in self.handlers:
            self.handlers[event](decoded["d"])

    def respond(self, event, data):
        self.send(jsonpickle.encode({
            "e": event,
            "d": data
        }, unpicklable=False))

    def send_message(self, sender, text):
        self.respond("message", {
            "sender": sender,
            "text": text
        })

    def send_message_to_all(self, sender, text):
        self.all(lambda player: player.consumer.send_message(sender, text))

    def apply_delta(self, delta):
        for pos, sprite in delta.items():
            x = int(pos.split(":")[0])
            y = int(pos.split(":")[1])

            self.sprites[y][x] = sprite

    def update(self, player):
        self.sprites = world.get_sprites()
        player.consumer.respond("delta", player.consumer.sprites)

    def delta(self, player):
        delta = world.get_delta(player.consumer.sprites)
        player.consumer.respond("update", delta)
        player.consumer.apply_delta(delta)

    def all(self, fun, *args, **kwargs):
        for player in players:
            fun(player, *args, **kwargs)

    def on_auth(self, data):
        if not data or "name" not in data:
            self.close()
            return

        name = data["name"] or f"Guest{random.randint(1, 10000):04}"
        self.player = Player(self, name)
        players.append(self.player)

        color = self.player.entity.sprite.fg
        welcome_msg = f"{self.player.get_fancy_name()} joined the game"
        players_list = ", ".join(player.get_fancy_name() for player in players)

        self.send_message_to_all("Server", welcome_msg)
        self.send_message("Online", players_list)

        self.update(self.player)
        self.all(self.delta)

    def on_move(self, data):
        if abs(data["dx"]) <= 1 and abs(data["dy"]) <= 1:
            self.player.entity.move(data["dx"], data["dy"])

    def on_chat(self, data):
        if data["message"]:
            self.send_message_to_all(self.player.get_fancy_name(), data["message"])
