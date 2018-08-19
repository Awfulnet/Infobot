"""
auth_ng commands.
* depends: auth_ng, ucmgr
"""

from .util.decorators import command
from .util import exc_line
from .auth_ng.data import NUH, AuthenticationError

def _get_tags(bot, nick):
    tags = bot.authmgr.tags_for_nick(nick)
    if tags:
        return f"auth tags for {nick}: {','.join(map(str, tags))}"
    else:
        return f"{nick} has no auth tags."

@command('auth.tags')
def get_tags(bot, nick, chan, arg):
    if arg:
        nick = arg

    bot.msg(chan, _get_tags(bot, nick))

def get_nuh_and_tags(bot, nick, chan, arg):
    to_nick, *rest = arg.split()

    if not rest:
        taglst = to_nick
        to_nick = nick
    else:
        taglst = rest[0]

    tags = taglst.split(',')

    try:
        user = bot.ucmgr.users[to_nick]
    except:
        bot.msg(chan, f"Unable to find nick {nick} - maybe wait until NAMES processing?")
        return None, None

    nuh = NUH.from_host(str(user))
    return nuh, tags


@command('auth.rm_tags', auth=True)
def rm_tag(bot, nick, chan, arg):
    nuh, tags = get_nuh_and_tags(bot, nick, chan, arg)
    if not nuh:
        return

    for tag in tags:
        try:
            bot.authmgr.rm_tag(nuh, tag)
        except AuthenticationError as e:
            return bot.msg(chan, exc_line(e))
    bot.msg(chan, _get_tags(bot, nuh.nick))

@command('auth.add_tags', auth=True)
def add_tag(bot, nick, chan, arg):
    nuh, tags = get_nuh_and_tags(bot, nick, chan, arg)
    if not nuh:
        return

    for tag in tags:
        try:
            bot.authmgr.add_tag(nuh, tag)
        except AuthenticationError as e:
            return bot.msg(chan, exc_line(e))
    bot.msg(chan, _get_tags(bot, nuh.nick))

