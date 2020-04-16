class Sender:
    def __init__(self):
        self.subscribers = []

    def __call__(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)

    def __iadd__(self, handler):
        self.subscribers.append(handler)
        return self

    def __isub__(self, handler):
        self.subscribers.remove(handler)
        return self
