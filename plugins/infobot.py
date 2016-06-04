"""
Info functionality

* depends: database
"""
from .util.decorators import command, init, process_privmsg
from .database import Database
from .sed import Substitution
from functools import wraps
from .util.data import get_doc
from functools import partial
import re
import traceback
import inspect
from functools import reduce
import gc

db = None

def caller():
    code_obj = inspect.stack()[1][0].f_code
    referrers = [x for x in gc.get_referrers(code_obj) if inspect.isfunction(x)]
    return referrers[0]

def addinfo(bot, pmsg):
    nick, chan, msg = process_privmsg(pmsg)

    m = re.search(r"^!add .+", msg)
    if not m:
        return

    if ' ' not in msg:
        return bot.msg(chan, "Usage: !add <info>")
    user, host = pmsg['host'].split("@")
    user = user.split("!")[1]

    info = msg.split(" ", 1)[1]
    if not bot.auth.is_authed(nick):
        return bot.notice(nick, "You are not registered with NickServ or not properly identified.")

    if 'alias' in info:
        alias = msg.split()[2]

        success = db.execute("SELECT addalias(%s, %s);", (nick, alias)).fetchone()[0]

        if not success:
            bot.notice(nick, "Error setting alias; you are creating an"
                " infinitely looping alias chain.")
        else:
            bot.notice(nick, "The info of your current nick %s now points to %s." % (nick, alias))

    else:
        db.execute("SELECT addinfo(%s, %s, %s, %s);", (nick, user, host, info))
        bot.notice(nick, "Info set to '%s'" % (info))

__callbacks__ = {"PRIVMSG": [addinfo]}


@command('info', '^(!|@)$name(\s|$)')
def getinfo(bot, nick, chan, gr, arg):
    """ !info <nick> -> get the info for a given user. """
    if not arg:
        return bot._msg(chan, get_doc())
    info = db.execute("SELECT nick, info FROM info(%s);", (arg,)).fetchone()
    if gr[0] == '@':
        msgfn = partial(bot._msg, chan)
    else:
        msgfn = partial(bot.notice, nick)

    if not info:
        return msgfn("No info found for {0}. Use '!add <info>' to add your info.".format(arg))

    if info[0].lower() == arg.lower():
        return msgfn("%s: %s" % (arg, info[1]))
    msgfn("%s →  %s: %s" % (arg, info[0], info[1]))

@command('del|rm', r'^!($name)(\s|$)')
def rmalias(bot, nick, chan, _, arg):
    """ !del <type> -> delete 'alias' or 'info' """
    if not arg or arg not in ('alias', 'info'):
        return bot._msg(chan, get_doc())

    if not bot.auth.is_authed(nick):
        return bot.notice(nick, "You are not registered with NickServ or not properly identified.")

    if arg == 'alias':
        db.execute("SELECT delalias(%s);", (nick,))
        bot.notice(nick, "Your nick now points to itself instead of to an alias.")
    else:
        db.execute("SELECT delinfo(%s);", (nick,))
        bot.notice(nick, "Deleted info.")

@command('append', r'^!$name(?:\s|$)', ppmsg=True)
def appendinfo(bot, nick, chan, arg, pmsg):
    """ !append <info> -> Append <info> to your info. """
    if not arg:
        return bot._msg(chan, get_doc())

    user, host = pmsg['host'].split("@")
    user = user.split("!")[1]

    if not bot.auth.is_authed(nick):
        return bot.notice(nick, "You are not registered with NickServ or not properly identified.")

    alias, info = db.execute("SELECT nick, info FROM info(%s)", (nick,)).fetchone()
    info += (" " + arg)
    db.execute("SELECT addinfo(%s, %s, %s, %s);", (alias, user, host, info))
    bot.notice(nick, "Info set to '%s'" % (info))

@command('sql', '^&$name .+', admin=True)
def execsql(bot, nick, chan, arg):
    db.execute(arg)
    try:
        bot._msg(chan, "%s" % ", ".join([str(list(i)) for i in db.fetchall()]))
    except:
       traceback.print_exc()

@command('sed', '^!$name .+', ppmsg=True)
def sedinfo(bot, nick, chan, arg, pmsg):
    # first, get the info for the current nick
    info = db.execute("SELECT nick, info FROM info(%s);", (nick,)).fetchone()

    user, host = pmsg['host'].split("@")
    user = user.split("!")[1]

    if not bot.auth.is_authed(nick):
        return bot.notice(nick, "You are not registered with NickServ or not properly identified.")

    try:
        sub = Substitution(arg)
    except TypeError as e:
        return bot.notice(nick, "Error: %s" % (e))

    newinfo = sub.do(info[1])

    if info[0].lower() != nick.lower():
        bot.notice(nick, "Note: because your current nick is an alias, your alias will"
                "be removed and your info will be set to %r." % (newinfo))

    db.execute("SELECT addinfo(%s, %s, %s, %s);", (nick, user, host, newinfo))
    bot.notice(nick, "Info set to '%s'" % (newinfo))

@init
def init(bot):
    global db
    db = bot.data["db"]
