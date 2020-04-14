import jsonpickle

from channels.generic.websocket import WebsocketConsumer

from .world import World

world = World(20, 20)
world.generate()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.handlers = {
            "auth": self.auth
        }

        self.accept();

        self.respond("update", world.tiles)

    def disconnect(self, close_code):
        pass

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

    def auth(self, data):
        if data:
            self.send_message("Server", "Successfully authorized")
        else:
            self.send_message("Server", "hmm?")
            self.close()
