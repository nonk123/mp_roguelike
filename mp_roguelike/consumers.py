from channels.generic.websocket import WebsocketConsumer

import random
import json

from .world import World, Entity

world = World(20, 20)
world.generate()

players = []

class Player:
    def __init__(self, consumer, name):
        self.consumer = consumer
        self.__name = name
        self.respawn()

    def __you(self):
        return self.entity.get_fancy_you()

    def show_death_message(self):
        msg = f"{self.get_fancy_name()} was killed by {self.entity.attacked_by.get_fancy_name()}"
        self.consumer.send_message_to_all("Game", msg)

    def show_dealt_damage(self, enemy, dmg):
        msg = f"{self.__you()} hit {enemy.get_fancy_name()} for {dmg} damage!"
        self.consumer.send_message("Game", msg)

    def show_taken_damage(self, dmg):
        msg = f"{self.entity.attacked_by.get_fancy_name()} hit {self.__you()} for {dmg} damage!"
        self.consumer.send_message("Game", msg)

    def show_dodged_message(self):
        self.consumer.send_message("Game", f"{self.__you()} have dodged!")

    def show_target_dodged_message(self, entity):
        self.consumer.send_message("Game", f"{entity.get_fancy_name()} has dodged!")

    def respawn(self):
        self.entity = Entity(self.__name)
        world.add_entity(self.entity)

        msg = f"{self.__you()} have {self.entity.hp} HP."
        self.consumer.send_message("Game", msg)

        self.entity.dead += self.show_death_message
        self.entity.dead += self.respawn
        self.entity.damaged += self.show_taken_damage
        self.entity.attacked += self.show_dealt_damage
        self.entity.dodged += self.show_dodged_message
        self.entity.target_dodged += self.show_target_dodged_message

    def get_fancy_name(self):
        return self.entity.get_fancy_name()

    def on_remove(self):
        self.entity.remove()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.handlers = {
            "auth": self.on_auth,
            "turn": self.on_turn,
            "chat": self.on_chat
        }

        self.accept();

        world.updated += self.delta_all

    def disconnect(self, close_code):
        if hasattr(self, "player") and self.player:
            goodbye_msg = f"{self.player.get_fancy_name()} disconnected"
            self.send_message_to_all("Server", goodbye_msg)

            self.player.on_remove()
            players.remove(self.player)

            self.delta_all()

    def receive(self, text_data):
        decoded = json.loads(text_data)

        event = decoded["e"]

        if event in self.handlers:
            self.handlers[event](decoded["d"])

    def respond(self, event, data):
        self.send(json.dumps({
            "e": event,
            "d": data
        }, default=lambda x: x.__dict__))

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

    def update(self, player=None):
        if not player:
            player = self.player

        player.consumer.sprites = world.get_sprites(self.player.entity)
        player.consumer.respond("update", player.consumer.sprites)

    def delta(self, player=None):
        if not player:
            player = self.player

        delta = world.get_delta(player.consumer.sprites, player.entity)
        player.consumer.respond("delta", delta)
        player.consumer.apply_delta(delta)

    def all(self, fun, *args, **kwargs):
        for player in players:
            fun(player, *args, **kwargs)

    def delta_all(self):
        self.all(self.delta)

    def on_auth(self, data):
        if not data or "name" not in data:
            self.close()
            return

        name = data["name"] or f"Guest{random.randint(1, 10000):04}"
        self.player = Player(self, name)
        players.append(self.player)

        welcome_msg = f"{self.player.get_fancy_name()} joined the game"
        players_list = ", ".join(player.get_fancy_name() for player in players)

        self.send_message_to_all("Server", welcome_msg)
        self.send_message("Online", players_list)

        self.update(self.player)
        self.all(self.delta)

    def on_move_turn(self, data):
        self.player.entity.queue_move(data["dx"], data["dy"])

    def on_turn(self, data):
        turn_handlers = {
            "move": self.on_move_turn
        }

        turn_type = data["turn_type"]

        if turn_type in turn_handlers:
            turn_handlers[turn_type](data["data"])

        world.update()

    def on_chat(self, data):
        if data["message"]:
            self.send_message_to_all(self.player.get_fancy_name(), data["message"])
