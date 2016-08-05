""" Initializer for the package utils. """

class DotDict(dict):
    def __getattribute__(self, name):
        if name in super().keys():
                return self[name]
        return super().__getattribute__(name)


def get_name(f):
    if type(f) == ModuleType:
        return f.__name__
    elif type(f) == FunctionType:
        return "%s.%s" % (inspect.getmodule(f).__name__, f.__name__)
    else:
        try:
            return f.__name__
        except AttributeError:
            return "unknown"

from types import ModuleType, FunctionType
import inspect
import datetime
def now():
	return datetime.datetime.utcnow()