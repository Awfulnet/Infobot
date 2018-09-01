from types import MethodType
import re
from .util.decorators import init

def wait_for(self, method: str, match_fn, callback):
    def message_fn(bot, msg):
        if match_fn(msg):
            callback(bot, msg)
            self.__irccallbacks__[method].remove(message_fn)

    self.register_callback(method, message_fn)

def wait_for_auth(bot, user, callback_fn):
    def message_fn(bot, msg):
        auth = bool(re.search(r"ACC\s[32]", msg["arg"]))
        callback_fn(auth)

    bot.msg('NickServ', 'ACC %s' % user)
    bot.wait_for("NOTICE", lambda m: 'NickServ!' in m['host'] and 'ACC' in m['arg'],
                 message_fn)


@init
def plugin_init(bot):
    bot.wait_for = MethodType(wait_for, bot)
