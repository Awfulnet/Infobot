from .util.decorators import init, command
from .util.data import sugar, lineify

import code
import datetime
import sys
import re

class IRCterpreter(code.InteractiveConsole):
    def __init__(self, localVars, botinstance):
        self.bot = botinstance
        self.curnick = ""
        self.curchan = ""
        self.cache = []
        self.TRACE_REGEX = re.compile(r"([A-Z][a-z]+Error|[A-Z][a-z]+Exception):?(?:\s+)?(.+)?")
        code.InteractiveConsole.__init__(self, localVars)

    def write(self, data):
        self.cache.append(data)

    def is_exception(self, data):
        return True if 'File "<console>", line ' in data else False

    def guru_meditate(self, traceback):
        match = self.TRACE_REGEX.search(traceback)
        if not match:
            return traceback
        exc_name, exc_args = match.groups()
        out = "⌜ \x02\x03such \x034%s \x03so \x034%s\x03\x02 ⌟" % (
            exc_name, exc_args)
        return out


    def flushbuf(self):
        out = "".join(self.cache).strip()

        if self.is_exception(out):
            # most likely a traceback, only capture exception
            print(out)
            out = self.guru_meditate(out.rsplit("\n", 1)[1])

        if len(out) > 0:
            for line in lineify(out):
                self.bot.msg(self.curchan, line)
        self.cache = []

    def run(self, nick, chan, code):
        if not "self" in self.locals.keys():
            self.locals["self"] = self
        self.locals["chan"] = chan
        self.locals["nick"] = nick
        self.curnick = nick
        self.curchan = chan
        sys.stdout = sys.interp = self
        self.push(code)
        sys.stdout = sys.__stdout__
        self.flushbuf()

@init
def init(bot):
    bot.data["interp_locals"] = locals()
    bot.data["interp_locals"].update(globals())
    bot.data["interp_locals"].update({"re": __import__("re"),
                                      "os": __import__("os")})
    bot.data["interp_locals"]['_dir'] = lambda x: [i for i in dir(x) if not i.startswith("__")]

@command('say', r'^&$name .+')
def cmd_say(bot, nick, chan, arg):
    if bot.verbose:
        print(datetime.datetime.utcnow())
    bot._msg(chan, arg)

cmd_say.__core__ = True #haxx

@command('raw', r'^&$name .+', admin=True)
def cmd_raw(bot, nick, chan, arg):
    bot._send(arg)

@command('join', r'^&$name #.+')
def cmd_join(bot, nick, chan, arg):
    bot._send("JOIN :%s" % (arg))

@command('part', r'^&$name$')
def cmd_part(bot, nick, chan, arg):
    bot._send("PART :%s" % (chan))

@command('quit', r'^&$name\s?(.+)?', admin=True)
def cmd_quit(bot, nick, chan, groups, arg):
    if groups[0] is not None:
        bot._send("QUIT :%s" % (groups[0]))
    else:
        bot._send("QUIT :bye")
    bot.gracefully_terminate()

@command('eval', r'^>> ', admin=True)
def cmd_eval(bot, nick, chan, arg):
    """ eval *args -> Evaluate *args as python code."""
    arg = sugar(arg)
    ip = None
    try:
        ip = bot.data["interp"]
    except KeyError:
        lcls = bot.data["interp_locals"]
        ip = bot.data["interp"] = IRCterpreter(lcls, bot)
    ip.run(nick, chan, arg)
