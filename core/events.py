import traceback

Standard = [
    {"WelcomeEvent": "welcome"},
    {"ModeEvent": "mode"},
    {"JoinEvent": "join"},
    {"PartEvent": "part"},
    {"MessageEvent": "message"},
    {"NoticeEvent": "notice"},
    {"ShutdownEvent": "shutdown"},
    {"KickEvent": "kick"},
    {"CommandCalledEvent": "cmd"}
]

class HandlerSet(set):
    def __getattribute__(self, name):
        x = {f.__name__:f for f in self}
        if name in x.keys():
            return x[name]
        return super().__getattribute__(name)

class AdvancedHandlerSet(HandlerSet):
    def __init__(self):
        self.disabled_set = HandlerSet()

    def disable(self, s):
        try:
            if hasattr(self, s):
                self.disabled_set.add(getattr(self, s))
                self.discard(getattr(self, s))
                return True
            else:
                return False
        except BaseException:
            return False

    def enable(self, s):
        try:
            if hasattr(self.disabled_set, s):
                self.add(getattr(self.disabled_set, s))
                self.disabled_set.discard(getattr(self.disabled_set, s))
                return True
            else:
                return False
        except BaseException:
            return False


class Event():
    """ A simple event class """
    def __init__(self, type_):
        self.handlers = AdvancedHandlerSet()
        self.type = type_

    def __str__(self):
        if len(self.handlers) != 1:
            return "Event(handlers=%s, ...}))" % (self.handlers.__str__().split(", ")[0])
        else:
            return "Event(handlers=%s)" % (self.handlers)

    def __repr__(self):
        return self.__str__()

    def register(self, handler):
        """ Register a function as an event handler """
        self.handlers.add(handler)
        return self

    def fire(self, *args, **kwargs):
        """ Fire this event """
        _kwargs = kwargs.copy()
        try:
            for handler in self.handlers:
                if not hasattr(handler, "_want_type"):
                    handler(*args, **kwargs)
                else:
                    kwargs.update({"type": self.type})
                    handler(*args, **kwargs)
                    kwargs = _kwargs
        except Exception as e:
            if type(e) == RuntimeError:
                # most likely a Set size changed during iteration thing.
                self.fire(*args, **kwargs)
            else:
                traceback.print_exc()

    def unhandle(self, handler):
        """ De-register an event handler from this event. Throws EventError"""
        try:
            self.handlers.remove(handler)
        except:
            raise EventError("Can't unhandle handler %s: \
                handler %s does not hook into this event!" % (handler, handler))


class EventError(BaseException):
    """ EventError class - When something goes wrong in an event."""
    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def __str__(self):
        return self.value
