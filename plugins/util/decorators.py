from plugins.auth import User
from inspect import getmodule
from functools import wraps
import re

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

def command(name, regex=None, cmdchar='&', admin=False, pass_privmsg=False):
    if not regex:
        regex = f'^{re.escape(cmdchar)}$name'

    if isinstance(regex, str):
        regex = regex.replace('$name', name)
        regex = re.compile(regex)

    def decorator(funct):
        @wraps(funct)
        def new_func(bot, privmsg):
            nick, chan, msg = process_privmsg(privmsg)

            match = regex.search(msg)
            arg = msg.split(' ', 1)[1] if ' ' in msg else ""

            if not match:
                return

            if admin and not bot.auth.isadmin(User.from_host(privmsg["host"])):
                return

            groups = match.groupdict() or match.groups()

            args = [bot, nick, chan]
            if groups: args.append(groups)
            args.append(arg)
            if pass_privmsg: args.append(privmsg)

            funct(*args)

        new_func.__core__ = False
        callback("PRIVMSG")(new_func)
        return new_func
    return decorator

