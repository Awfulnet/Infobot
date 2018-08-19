from .data import Action, AuthRes
import traceback

class Tag:
    def __new__(cls, *args):
        instance = super().__new__(cls)
        instance._args = args
        return instance

    def try_auth(self, *args):
        try:
            retval = self._try_auth(*args)
            if not retval:
                return AuthRes.CONTINUE
            else:
                return retval
        except:
            traceback.print_exc()
            return AuthRes.CONTINUE

    def __repr__(self):
        if self._args:
            return f"{type(self).__name__.lower()}:{':'.join(self._args)}"
        else:
            return type(self).__name__.lower()

class All(Tag):
    def _try_auth(*args):
        return AuthRes.SUCCESS

class Module(Tag):
    def __init__(self, module_name):
        self.module_name = module_name

    def _try_auth(self, bot, action, data, host):
        if not hasattr(data, "__module__"):
            return

        if action == Action.COMMAND_CALL and \
           data.__module__.split('.')[1] == self.module_name:
               return AuthRes.SUCCESS

class Command(Tag):
    def __init__(self, command_name):
        self.command_name = command_name

    def _try_auth(self, bot, action, data, host):
        if not hasattr(data, "__name__") or \
           not hasattr(data, "__module__"):
               return

        if action == Action.COMMAND_CALL and data.cmd_name == self.command_name:
            return AuthRes.SUCCESS
