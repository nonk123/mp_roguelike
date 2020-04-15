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

    def _clear_all_handlers(self):
        for key in self._handlers:
            self._handlers[key] = []

    cls.__init__ = __init__
    cls._clear_all_handlers = _clear_all_handlers
    cls.on = on

    return cls

def event(fun):
    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        # Save `self._handlers' in case it gets cleared when calling `fun'.
        handlers = [handler for handler in self._handlers[fun.__name__]]

        ret = fun(self, *args, **kwargs)

        for handler in handlers:
            handler(self)

        return ret

    wrapper.__event_flag = True

    return wrapper
