from .util.decorators import command, init, process_privmsg
from .database import Database
from functools import wraps
from .util.data import get_doc
from functools import partial
import re
import traceback
import inspect
import gc

db = None

pending_adds = {}
pending_alias_adds = {}
pending_appends = {}
pending_rmalias = []
pending_rminfo = []

def caller():
    code_obj = inspect.stack()[1][0].f_code
    referrers = [x for x in gc.get_referrers(code_obj) if inspect.isfunction(x)]
    return referrers[0]

def insert_callback(bot, ctype, func):
    try:
        bot.__irccallbacks__[ctype].append(func)
    except KeyError:
        bot.__irccallbacks__[ctype] = [func]

def notice_listener(bot, msg):
    message = msg["arg"].split(" ", 1)[1][1:]
    sender = msg["host"].split("!")[0]

    if sender.lower() != "nickserv" or "ACC" not in message:
        return
    if "ACC" in message and not message.endswith("3"):
        nick = message.split()[0]
        pending_adds.pop(nick, None)
        pending_alias_adds.pop(nick, None)
        pending_appends.pop(nick, None)
        try:
            pending_rmalias.remove(nick)
        except ValueError:
            pass
        try:
            pending_rminfo.remove(nick)
        except ValueError:
            pass

    nick = message.split()[0]
    if nick in pending_adds:
        user, host, info = pending_adds[nick]
        db.execute("SELECT addinfo(%s, %s, %s, %s);", (nick, user, host, info))
        del pending_adds[nick]
        bot.notice(nick, "Info set to '%s'" % (info))
    if nick in pending_appends:
        user, host, toappend = pending_appends[nick]
        alias, info = db.execute("SELECT nick, info FROM info(%s)", (nick,)).fetchone()
        info += (" " + toappend)
        db.execute("SELECT addinfo(%s, %s, %s, %s);", (alias, user, host, info))
        bot.notice(nick, "Info set to '%s'" % (info))
        del pending_appends[nick]
    if nick in pending_alias_adds:
        alias = pending_alias_adds[nick]
        success = db.execute("SELECT addalias(%s, %s);", (nick, alias)).fetchone()[0]
        if not success:
            bot.notice(nick, "Error setting alias; you are creating an"
                " infinitely looping alias chain.")
        else:
            bot.notice(nick, "The info of your current nick %s now points to %s." % (nick, alias))
        del pending_alias_adds[nick]
    if nick in pending_rmalias:
        pending_rmalias.remove(nick)
        db.execute("SELECT delalias(%s);", (nick,))
        bot.notice(nick, "Your nick now points to itself instead of to an alias.")
    if nick in pending_rminfo:
        pending_rminfo.remove(nick)
        db.execute("SELECT delinfo(%s);", (nick,))
        bot.notice(nick, "Deleted info.")
   
def addinfo(bot, pmsg):
    nick, chan, msg = process_privmsg(pmsg)
    
    m = re.search(r"^!add .+", msg)
    if not m:
        return

    if ' ' not in msg:
        return bot.msg(chan, "Usage: !add <info>")
    user, host = pmsg['host'].split("@")
    user = user.split("!")[0]

    info = msg.split(" ", 1)[1]
    if 'alias' in info:
        pending_alias_adds[nick] = msg.split()[2]
    else:
        pending_adds[nick] = (user, host, info)
    bot._msg("NickServ", "ACC %s" % (nick))

__callbacks__ = {"PRIVMSG": [addinfo], "NOTICE": [notice_listener]}

@init
def init(bot):
    global db
    db = Database(password=bot.config["dbpass"], host=bot.config["dbhost"])
    bot.data["db"] = db


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
    if arg == 'alias':
        pending_rmalias.append(nick)
    else:
        pending_rminfo.append(nick)
    bot._msg("NickServ", "ACC %s" % (nick))

@command('append', r'^!$name(?:\s|$)', ppmsg=True)
def appendinfo(bot, nick, chan, arg, pmsg):
    """ !append <info> -> Append <info> to your info. """
    if not arg:
        return bot._msg(chan, get_doc())
    
    user, host = pmsg['host'].split("@")
    user = user.split("!")[0]
    
    pending_appends[nick] = (user, host, arg)
    bot._msg("NickServ", "ACC %s" % (nick))

@command('sql', '^&$name .+', admin=True)
def execsql(bot, nick, chan, arg):
    db.execute(arg)
    bot._msg(chan, "%s" % (db.fetchall()))
