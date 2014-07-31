from functools import wraps

def startinfo(*args):
    """ The startinfo decorator """
    def decorator(funct):
        """ The actual decorator """
        james_version = args[0]

        @wraps(funct)
        def wrapper(*args, **kwargs):
            """ Some other sort of decorating thing """
            print("James version %s initializing..." % (james_version))
            return funct(*args, **kwargs)
        return wrapper
    return decorator


def IRCCallback(*hooks):
    def decorator(funct):
        funct.__core__ = True
        if "return" in funct.__annotations__:
            raise Warning("IRCCallback mutilates function annotations, "
                "but a return annotation is already defined.")
        funct.__annotations__["return"] = hooks
        return funct
    return decorator