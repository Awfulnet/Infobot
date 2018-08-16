from functools import wraps
from inspect import getmembers, isclass

def method_wrapper(bases, cls, method):
    """
    Wraps a class method to map base class return values to subclass return values.
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        if type(result) in bases:
            return cls(result)
        else:
            return result
    return wrapper

class TypePreservingMeta(type):
    """
    Metaclass that enforces the requirement that types are preserved when
    applying operators to a type.

    i.e. ModeSet() | {'a'} is of type ModeSet, not of type set.
    """
    def __new__(cls, name, bases, clsdict):
        clsobj = super().__new__(cls, name, bases, dict(clsdict))
        for name, method in getmembers(clsobj,
                predicate=lambda mb: callable(mb) and not isclass(mb)):
            if (name == '__new__'):
                # Wrapping new can get us into some recursive trouble.
                continue
            setattr(clsobj, name, method_wrapper(clsobj.mro(), clsobj, method))
        return clsobj

class TypePreserving(metaclass=TypePreservingMeta):
    """ A type-preserve mixin. """
    pass

class StringSet(set):
    def __init__(self, contents=None):
        contents = contents or set()
        for item in contents:
            if not isinstance(item, str):
                raise TypeError("Set items have to be strings.")
        super().__init__(contents)
