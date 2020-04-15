import jsonpickle

from channels.generic.websocket import WebsocketConsumer

import functools

from .world import World, Entity

world = World(20, 20)
world.generate()

players = []

class Player:
    def __init__(self, consumer):
        self.consumer = consumer
        self.entity = Entity()
        world.add_entity(self.entity)

    def update(self):
        self.consumer.update()

    def on_remove(self):
        self.entity.remove()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.handlers = {
            "auth": self.on_auth
        }

        self.accept();

    def disconnect(self, close_code):
        if self.player:
            self.player.on_remove()
            players.remove(self.player)

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

    def update(self):
        self.respond("update", world.get_sprites())

    def on_auth(self, data):
        if not data:
            self.close()
            return

        self.send_message("Server", "Successfully authorized")
        self.player = Player(self)
        players.append(self.player)

        for player in players:
            player.update()
