from inspect import getmodule
from functools import wraps
import re

class User():
    pass

def init(funct):
    m = getmodule(funct)
    if hasattr(m, '__inits__'):
        m.__inits__.append(funct)
    else:
        setattr(m, '__inits__', [funct])
    return funct

def callback(cbtype):
    def decorator(funct):
        m = getmodule(funct)
        if hasattr(m, '__callbacks__'):
            if cbtype in m.__callbacks__:
                m.__callbacks__[cbtype].append(funct)
            else:
                m.__callbacks__[cbtype] = [funct]
        else:
            m.__callbacks__ = {cbtype: [funct]}
        return funct
    return decorator

def process_privmsg(msg):
    nick = msg["host"].split('!')[0]
    chan = msg["arg"].split()[0]
    chan = chan.lower()
    if not chan.startswith("#"):
        # Private message. File under sender.
        chan = nick
    msg = msg["arg"].split(":", 1)[1]
    return (nick, chan, msg)

def command(name, regex, admin=False, ppmsg=False):
    if type(regex) == type(''):
        regex = regex.replace('$name', name)
        regex = re.compile(regex)
    def decorator(funct):
        @wraps(funct)
        def new_func(bot, pmsg):
            nick, chan, msg = process_privmsg(pmsg)
            m = regex.search(msg)
            if ' ' in msg:
                arg = msg.split(' ', 1)[1]
            else:
                arg = ""
            if not m:
                return

            if not bot.auth.isadmin(User.from_host(pmsg["host"])) and admin:
                return

            groups = m.groupdict() or m.groups()

            if groups:
                if ppmsg:
                    funct(bot, nick, chan, groups, arg, pmsg)
                else:
                    funct(bot, nick, chan, groups, arg)
            else:
                if ppmsg:
                    funct(bot, nick, chan, arg, pmsg)
                else:
                    funct(bot, nick, chan, arg)
        new_func.__core__ = False
        callback("PRIVMSG")(new_func)
        return new_func
    return decorator

from plugins.auth import User
