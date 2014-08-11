from .util.decorators import command, init, process_privmsg
from .database import Database
from functools import wraps
from .util.data import get_doc
from functools import partial
import re

db = None

old_callbacks = None
pending_adds = {}
pending_alias_adds = {}
pending_appends = {}

def insert_callback(bot, ctype, cback):
    global old_callbacks
    old_callbacks = bot.__irccallbacks__.get(ctype, None)
    bot.register_callback(ctype, cback)

def restore_callbacks(bot, ctype):
    if old_callbacks == None:
        del bot.__irccallbacks__[ctype]
        return
    bot.__irccallbacks__[ctype] = old_callbacks

def nlistener_base(funct):
    @wraps(funct)
    def new_func(bot, msg):
        message = msg["arg"].split(" ", 1)[1][1:]
        sender = msg["host"].split("!")[0]

        if sender.lower() == 'nickserv' and message.endswith("ACC 3"):
            funct(bot, msg, message, sender)
    return new_func

@nlistener_base
def add_notice_listener(bot, msg, message, sender):
    nick = message.split()[0]
    user, host, info = pending_adds[nick]
    db.execute("SELECT addinfo(%s, %s, %s, %s);", (nick, user, host, info))
    del pending_adds[nick]
    bot.notice(nick, "Info set to '%s'" % (info))
    restore_callbacks(bot, "NOTICE")

@nlistener_base
def addalias_notice_listener(bot, msg, message, sender):
    nick = message.split()[0]
    alias = pending_alias_adds[nick]
    success = db.execute("SELECT addalias(%s, %s);", (nick, alias)).fetchone()[0]
    if not success:
        bot.notice(nick, "Error setting alias; you are creating an"
            " infinitely looping alias chain.")
    else:
        bot.notice(nick, "The info of your current nick %s now points to %s." % (nick, alias))
    del pending_alias_adds[nick]
    restore_callbacks(bot, "NOTICE")

@nlistener_base
def rmalias_notice_listener(bot, msg, message, sender):
    nick = message.split()[0]
    db.execute("SELECT delalias(%s);", (nick,))
    bot.notice(nick, "Your nick now points to itself instead of to an alias.")
    restore_callbacks(bot, "NOTICE")

@nlistener_base
def rminfo_notice_listener(bot, msg, message, sender):
    nick = message.split()[0]
    db.execute("SELECT delinfo(%s);", (nick,))
    bot.notice(nick, "Deleted info.")
    restore_callbacks(bot, "NOTICE")

@nlistener_base
def append_notice_listener(bot, msg, message, sender):
    nick = message.split()[0]
    curinfo = db.execute("SELECT info FROM info(%s)", (nick,)).fetchone()[0]
    user, host, info = pending_appends[nick]
    curinfo += (" " + info)
    db.execute("SELECT addinfo(%s, %s, %s, %s);", (nick, user, host, curinfo))
    bot.notice(nick, "Info set to '%s'" % (curinfo))
    del pending_appends[nick]
    restore_callbacks(bot, "NOTICE")

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
        insert_callback(bot, "NOTICE", addalias_notice_listener)
    else:
        pending_adds[nick] = (user, host, info)
        insert_callback(bot, "NOTICE", add_notice_listener)
    bot._msg("NickServ", "ACC %s" % (nick))

__callbacks__ = {"PRIVMSG": [addinfo]}

@init
def init(bot):
    global db
    db = Database(password=bot.config["dbpass"])
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
        insert_callback(bot, "NOTICE", rmalias_notice_listener)
    else:
        insert_callback(bot, "NOTICE", rminfo_notice_listener)
    bot._msg("NickServ", "ACC %s" % (nick))

@command('append', r'^!$name(?:\s|$)', ppmsg=True)
def appendinfo(bot, nick, chan, arg, pmsg):
    """ !append <info> -> Append <info> to your info. """
    if not arg:
        return bot._msg(chan, get_doc())
    
    user, host = pmsg['host'].split("@")
    user = user.split("!")[0]
    
    pending_appends[nick] = (user, host, arg)
    insert_callback(bot, "NOTICE", append_notice_listener)
    bot._msg("NickServ", "ACC %s" % (nick))

@command('sql', '^&$name .+', admin=True)
def execsql(bot, nick, chan, arg):
    db.execute(arg)
    bot._msg(chan, "%s" % (db.fetchall()))
