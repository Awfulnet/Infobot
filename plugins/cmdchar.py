from .util.decorators import command, init
from .util.data import get_doc
from functools import partial

@command('cmdchars', '^!$name$')
def get_cmdchars(bot, nick, chan, arg):
    """ !cmdchars -> get all cmdchars currently in use """
    info = bot.data["db"].execute("SELECT cmdchar, string_agg(bot, ', ' ORDER BY bot) \
                                   FROM bots GROUP BY cmdchar;").fetchall()

    for item in info:
        item = list(item)
        item[0] = "\x0302%s\x0F" % (item[0])
        item[1] = "\x0310%s\x0F" % (item[1])
        bot.notice(nick, "%s — %s" % tuple(item))

@command('bots', '^!$name$')
def get_bots(bot, nick, chan, arg):
    """ !bots -> get all bots that are known to the db """
    info = bot.data["db"].execute("SELECT bot, owner, string_agg(cmdchar, ' ' ORDER BY cmdchar) \
                                   FROM bots GROUP BY bot, owner;").fetchall()

    for item in info:
        item = list(item)
        item[0] = "\x0302%s\x0F" % (item[0])
        item[1] = "\x0310%s\x0F" % (item[1])
        item[2] = "\x0311%s\x0F" % (item[2])
        bot.notice(nick, "%s [%s] - %s" % tuple(item))


@command('bot', '^(!|@)$name\s')
def get_bot(bot, nick, chan, gr, arg): 
    """ {!@}bot <bot name> -> get information about a bot in the db """
    if not arg:
        bot.msg(chan, get_doc())
    msg_fn = partial(bot.notice, nick) if (gr[0] == '!') else partial(bot.msg, chan)

    info = bot.data["db"].execute("SELECT bot, owner, string_agg(cmdchar, ' ' ORDER BY cmdchar) \
                                   FROM bots WHERE bot = %s GROUP BY bot, owner;", (arg,)).fetchone();

    if not info:
        msg_fn("%s is an unknown bot." % (arg))
    else:
        bot_nick = "\x0302%s\x0F" % (info[0])
        owner = "\x0310%s\x0F" % (info[1])
        cmdchars = "\x0311%s\x0F" % (info[2])
        
        msg_fn("%s [%s] - %s" % (bot_nick, owner, cmdchars))

@command('cmdchar.used', "^(!|@)$name")
def is_cmdchar_used(bot, nick, chan, gr, arg):
    """ {!@}cmdchar.used <cmdchar> -> tells you whether the cmdchar you passed in is used already """
    if not arg:
        bot.msg(chan, get_doc())

    msg_fn = partial(bot.notice, nick) if (gr[0] == '!') else partial(bot.msg, chan)

    info = bot.data["db"].execute("SELECT bot FROM bots WHERE cmdchar = %s;", (arg,)).fetchall()
    if not info:
        msg_fn("%s is unused." % (arg))
    else:
        msg_fn("%s is used by %s" % (arg, ', '.join([i[0] for i in info])))

@command('cmdchar.add', '^(!|@)$name')
def add_cmdchar(bot, nick, chan, gr, arg):
    """ {!@}cmdchar.add <cmdchar> <bot> -> add a bots entry """
    if not arg:
        bot.msg(chan, get_doc())

    msg_fn = partial(bot.notice, nick) if (gr[0] == '!') else partial(bot.msg, chan)
    args = arg.split()

    already_exists = bot.data["db"].execute("SELECT bot FROM bots WHERE cmdchar = %s", args[0]).fetchall()

    bot.data["db"].execute("INSERT INTO bots (cmdchar, bot, owner) VALUES \
       (%s, %s, %s);", (args[0], args[1], nick))

    if bot.data["db"].rowcount:
        if already_exists:
            msg_fn("Command char %s added to %s (also used by: %s)" % (args[0], args[1], ', '.join([i[0] for i in already_exists])))
        else:
            msg_fn("Command char %s added to %s" % (args[0], args[1]))
    else:
        msg_fn("Command char %s is already used by %s!" % (args[0], args[1]))
