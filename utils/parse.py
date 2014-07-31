"""
IRC Parser - parse.py
"""

import inspect
import traceback
import re
import subprocess
import sys

SED_REGEX = re.compile(r"^(?:(\S+)[:,])?(?:(.+?)/)?s/(.+?)/([^/]+)/?(?:([gixs]{0,4}))?")

def parse(msg):
    """ Parse an IRC protocol message """
    if msg.startswith("PING"):
        info = {"method": "PING", "arg": msg.split()[-1]}
    else:
        splitmsg = msg.split(" ", 2)
        info = {"method": splitmsg[1], "host": splitmsg[0][1:], "arg":
                splitmsg[2]}
    return info

def evaluate(self, nick, chan, msg):
    """ Evaluate python code. """
    try:
        output = eval(msg, globals(), locals())
        if output is not None:
            self.leo = output
            if type(self.leo) == tuple:
                self.leo = list(self.leo)
                output = list(output)
            return output
    except (NameError, SyntaxError):
        try:
            exec(msg, globals())
        except:
            try:
                exec(msg, locals())
            except:
                try:
                    exec(msg,globals(),locals())
                except:
                    exec(msg,locals(),globals())

###
##
## Sed part
##
###

def populate(sedobject, groups):
    group_types = ("target", "qual", "to_replace", "replacement", "flags")
    for k, v in zip(group_types, groups):
        setattr(sedobject, k, v)

def set_flags(sedobject, flags):
    i = 0
    count = 1

    if not flags:
        setattr(sedobject, "flags", i)
        setattr(sedobject, "count", count)
        return

    for item in flags:
        if item == "i":
            i |= re.IGNORECASE
        if item == "x":
            i |= re.X
        if item == "s":
            i |= re.S
        if item == "g":
            count = 0

    setattr(sedobject, "flags", i)
    setattr(sedobject, "count", count)

def debug(sedobject):
    for k,v in sedobject.__dict__.items():
        if not k.startswith("_") or not k.endswith("_"):
            print("%s: %s" % (k,v))

def get_message(bot, sedregex, nick, chan, qual=None):
    if not nick in bot.state.messages:
        return ""
    for message in bot.state.messages[nick]:
        if not message.channel == bot.state.channels[chan]:
            continue
        msg = message.msg
        try:
            if qual:
                if re.search(sedregex, msg) and re.search(qual, msg) and not SED_REGEX.search(msg):
                    return msg
            else:
                if re.search(sedregex, msg) and not SED_REGEX.search(msg):
                    return msg
        except BaseException:
            pass
    return ""

def sed(bot, nick, chan, msg):
    """ Perform the sedding """
    s = type("SedObject", tuple(), {})
    #[print(i) for i in (bot, nick, chan, msg)]
    
    if not SED_REGEX.match(msg):
        return

    groups = SED_REGEX.match(msg).groups()
    populate(s, groups)
    set_flags(s, s.flags)

    if bot.debug:
        debug(s)

    if s.target:
        nick = s.target

    nick = nick.lower()

    if s.qual:
        s.msg = get_message(bot, s.to_replace, nick, chan, qual=s.qual)
    else:
        s.msg = get_message(bot, s.to_replace, nick, chan)

    if not s.msg: return

    try:

        new_msg = re.sub(s.to_replace, s.replacement, s.msg, s.count, s.flags)
        if '\x01' in new_msg:
            # probably a message with a CTCP ACTION in it.
            new_msg = new_msg.split(" ", 1)[1][:-1]
            return bot.msg(chan, "* %s %s" % (nick, new_msg))

        return bot.msg(chan, "<%s> %s" % (nick, new_msg))
    except BaseException:
        traceback.print_exc()
    
