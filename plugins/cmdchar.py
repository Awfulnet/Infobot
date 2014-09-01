from .util.decorators import command, init
from .util.data import get_doc
from functools import partial

@command('cmdchars', '^!$name$')
def get_cmdchars(bot, nick, chan, arg):
    """ !cmdchars -> get all cmdchars currently in use """
    info = bot.data["db"].execute("SELECT cmdchar, bot, owner FROM bots;").fetchall()
    for item in info:
        item = list(item)
        item[0] = "\x0302%s\x0F" % (item[0])
        item[1] = "\x0310%s\x0F" % (item[1])
        item[2] = "\x0311%s\x0F" % (item[2])
        bot.notice(nick, "%s —  %s [%s]" % tuple(item))

@command('cmdchar.used', "^(!|@)$name")
def is_cmdchar_used(bot, nick, chan, gr, arg):
    """ !cmdchar.used -> tells you whether the cmdchar you passed in is used already """
    if not arg:
        bot.msg(chan, get_doc())
    msg_fn = None
    if gr[0] == '!':
        msg_fn = partial(bot.notice, nick)
    else:
        msg_fn = partial(bot.msg, chan)

    info = bot.data["db"].execute("SELECT bot, owner FROM bots WHERE cmdchar = %s;", (arg,)).fetchone()
    if not info:
        msg_fn("%s is unused." % (arg))
    else:
        msg_fn("%s is used by %s (owned by %s)" % (arg, info[0], info[1]))

@command('cmdchar.add', '^(!|@)$name')
def add_cmdchar(bot, nick, chan, gr, arg):
    """ !cmdchar.add <cmdchar> <bot> -> add a bots entry """
    if not arg:
        bot.msg(chan, get_doc())
    msg_fn = None
    if gr[0] == '!':
        msg_fn = partial(bot.notice, nick)
    else:
        msg_fn = partial(bot.msg, chan)

    args = arg.split()

    bot.data["db"].execute("INSERT INTO bots (cmdchar, bot, owner) VALUES \
       (%s, %s, %s);", (args[0], args[1], nick))
    msg_fn("Inserted values.")
