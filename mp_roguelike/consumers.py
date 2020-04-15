import jsonpickle

from channels.generic.websocket import WebsocketConsumer

from .world import World, Entity

world = World(20, 20)
world.generate()

players = []

class Player:
    def __init__(self, consumer):
        self.consumer = consumer
        self.entity = Entity()
        world.add_entity(self.entity)

    def on_remove(self):
        self.entity.remove()

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.handlers = {
            "auth": self.on_auth,
            "move": self.on_move
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
        if not data:
            self.close()
            return

        self.send_message("Server", "Successfully authorized")
        self.player = Player(self)
        players.append(self.player)

        self.update(self.player)
        self.all(self.delta)

    def on_move(self, data):
        if abs(data["dx"]) <= 1 and abs(data["dy"]) <= 1:
            self.player.entity.move(data["dx"], data["dy"])
            self.all(self.delta)
