import functools

class EventListener:
    def __init__(self, sender, event, handler):
        self.sender = sender
        self.event = event
        self.handler = handler

    def remove(self):
        self.sender._handlers[self.event].remove(self.handler)

def sender(cls):
    original_init = cls.__init__

    @functools.wraps(original_init)
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        self._handlers = {}
        self._events = []

        for fun in map(lambda name: getattr(self, name), dir(self)):
            if callable(fun) and hasattr(fun, "__event_flag") and fun.__event_flag:
                self._events.append(fun.__name__)
                self._handlers[fun.__name__] = []

    def on(self, event, handler):
        if event not in self._events:
            raise Exception("Not an event: %s" % event)
        else:
            self._handlers[event].append(handler)
            return EventListener(self, event, handler)

    cls.__init__ = __init__
    cls.on = on

    return cls

def event(fun):
    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        ret = fun(self, *args, **kwargs)

        for handler in self._handlers[fun.__name__]:
            handler(self)

        return ret

    wrapper.__event_flag = True

    return wrapper
