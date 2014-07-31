""" Initializer for the package utils. """

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

from . import command
from . import commandhandler
from . import parse
from . import num
from . import events
from . import message
from . import channel
from types import ModuleType, FunctionType
import inspect
import datetime
def now():
	return datetime.datetime.utcnow()