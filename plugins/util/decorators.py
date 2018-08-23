from plugins.auth import User
from inspect import getmodule
from functools import wraps
import re
import logging
import traceback

from .data import CommandException

logger = logging.getLogger("util")

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

def try_auth_ng_import():
    global AUTH_NG, Action, AuthRes
    try:
        from plugins.auth_ng.data import Action, AuthRes
        AUTH_NG = True
    except ImportError:
        traceback.print_exc()
        logger.warn("Missing auth_ng plugin, so tag-based auth won't work.")
        AUTH_NG = False

def command(name, regex=None, cmdchar='&', admin=False, pass_privmsg=False, auth=False):
    if auth:
        try_auth_ng_import()

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

            if auth and not AUTH_NG:
                return

            if auth:
                res = bot.authmgr.try_auth(Action.COMMAND_CALL, new_func, privmsg["host"])
                if res == AuthRes.FAIL:
                    return

            if admin and not bot.auth.isadmin(User.from_host(privmsg["host"])):
                return


            groups = match.groupdict() or match.groups()

            args = [bot, nick, chan]
            if groups: args.append(groups)
            args.append(arg)
            if pass_privmsg: args.append(privmsg)

            try:
                funct(*args)
            except CommandException as e:
                error, send_doc = e.args
                bot.msg(chan, f"\x034Error: {error}")
                if hasattr(funct, "__doc__") and send_doc:
                    bot.msg(chan, f"Usage: {funct.__doc__.strip()}")

        new_func.__core__ = False
        new_func.cmd_name = name
        callback("PRIVMSG")(new_func)
        return new_func
    return decorator

