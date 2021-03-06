from channels.generic.websocket import WebsocketConsumer

import random
import json

from .util import Die
from .world import world
from .entities import Entity
from .ai import ControlledAI

players = []

PLAYER_COLORS = ["red", "green", "blue", "yellow", "darkgray"]

class Player:
    def __init__(self, consumer, name):
        self.consumer = consumer
        self.__name = name
        self.__color = PLAYER_COLORS[len(players) % len(PLAYER_COLORS)]

        world.entity_died += self.show_death_message

    def show_death_message(self, entity):
        if entity not in self.entity.get_visible_entities():
            return

        msg = f"{entity.fancy_name} was killed by {entity.attacked_by.fancy_name}"
        self.consumer.send_message_to_all("Game", msg)

    def show_dealt_damage(self, enemy, dmg):
        msg = f"{self.entity.fancy_you} hit {enemy.fancy_name} for {dmg} damage!"
        self.consumer.send_message("Game", msg)

    def show_taken_damage(self, dmg):
        msg = f"{self.entity.attacked_by.fancy_name} hit {self.entity.fancy_you} for {dmg} damage!"
        self.consumer.send_message("Game", msg)

    def show_dodged_message(self):
        self.consumer.send_message("Game", f"{self.entity.fancy_you} have dodged!")

    def show_target_dodged_message(self, entity):
        self.consumer.send_message("Game", f"{entity.fancy_name} has dodged!")

    def respawn(self):
        self.entity = Entity({
            "name": self.__name,
            "character": "@",
            "color": self.__color,
            "ai_type": ControlledAI,
            "hp_roll": Die(3, 8, +40),
            "attack_roll": Die(2, 6, +2),
            "view_radius": 10
        })

        world.add_entity(self.entity)

        self.entity.dead += self.respawn
        self.entity.damaged += self.show_taken_damage
        self.entity.attacked += self.show_dealt_damage
        self.entity.dodged += self.show_dodged_message
        self.entity.target_dodged += self.show_target_dodged_message

def update_all():
    for player in players:
        player.consumer.update()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.handlers = {
            "auth": self.on_auth,
            "turn": self.on_turn,
            "chat": self.on_chat
        }

        self.accept();

    def disconnect(self, close_code):
        if hasattr(self, "player") and self.player:
            goodbye_msg = f"{self.player.entity.fancy_name} disconnected"
            self.send_message_to_all("Server", goodbye_msg)

            self.player.entity.remove()
            players.remove(self.player)

            update_all()

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

    def all(self, fun, *args, **kwargs):
        for player in players:
            fun(player, *args, **kwargs)

    def update(self, player=None):
        if not player:
            player = self.player

        tiles, entities = player.entity.get_renderable()

        player.consumer.respond("update", {
            "tiles": tiles,
            "entities": entities,
            "player": player.entity.stripped()
        })

    def on_auth(self, data):
        if not data or "name" not in data:
            return self.close()

        name = data["name"] or f"Guest{random.randint(1, 10000):04}"
        self.player = Player(self, name)
        players.append(self.player)
        self.player.respawn()

        welcome_msg = f"{self.player.entity.fancy_name} joined the game"
        players_list = ", ".join(player.entity.fancy_name for player in players)

        self.send_message_to_all("Server", welcome_msg)
        self.send_message("Online", players_list)

        update_all()

    def on_move_turn(self, data):
        self.player.entity.ai.move(data["dx"], data["dy"])

    def on_turn(self, data):
        turn_handlers = {
            "move": self.on_move_turn
        }

        turn_type = data["turn_type"]

        if turn_type in turn_handlers:
            turn_handlers[turn_type](data["data"])

        world.update()

        update_all()

    def on_chat(self, data):
        if data["message"]:
            self.send_message_to_all(self.player.entity.fancy_name, data["message"])
