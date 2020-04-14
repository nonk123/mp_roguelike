import json

from channels.generic.websocket import WebsocketConsumer

class RoguelikeConsumer(WebsocketConsumer):
    def connect(self):
        self.accept();
        self.send(text_data=json.dumps(list(self.generate_tiles(50, 50))))

    def generate_tiles(self, w, h):
        for y in range(h):
            row = []

            for x in range(w):
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    c = "#"
                else:
                    c = "."

                row.append({
                    "character": c
                })

            yield row

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        pass
