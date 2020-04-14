import jsonpickle

from channels.generic.websocket import WebsocketConsumer

from .world import World

world = World(20, 20)
world.generate()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.accept();
        self.send(text_data=self.serialize(world.tiles))

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        pass

    def serialize(self, obj):
        return jsonpickle.encode(obj, unpicklable=False)
