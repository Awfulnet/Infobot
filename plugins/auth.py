"""
Infobot Authentication Module
"""

import re
import threading
import sys
from functools import partial

def printish(stuff):
    sys.__stdout__.write(stuff + '\n')
    sys.__stdout__.flush()

def auth_notify_fn(bot, msg, condition=None, authed=None):
    condition.acquire()

    if re.search(r"ACC\s[32]", msg["arg"]):
        authed.append(True)
    else:
        authed.append(False)

    condition.notify()
    condition.release()


class User(object):
    def __init__(self, nick, user, host):
        self.nick = nick
        self.user = user
        self.host = host

    @staticmethod
    def from_host(msg):
        ms = re.search("^:?(.+?)!(.+?)@(.+)", msg).groups()
        return User(*ms)

    def __repr__(self):
        return "%s!%s@%s" % (self.nick, self.user, self.host)

class Authenticator(object):
    def __init__(self):
        self.admins = {}
        self.bot = None

        self.wakeupCond = threading.Condition()

    def isadmin(self, person):
        return True if person.nick in self.admins and self.admins[person.nick].host == person.host else False

    def addadmin(self, *person):
        as_user = User(*person)
        self.admins[as_user.nick] = as_user

    def rmadmin(self, person):
        del self.admins[person.nick]

    def nick(self, bot, msg):
        """ Handles nickchanges """
        oldnick = msg["host"].split("!")[0]
        newnick = msg["arg"][1:]

        if newnick in self.admins and oldnick not in self.admins:
            return

        if oldnick in self.admins:
            self.admins[newnick] = self.admins[oldnick]

            del self.admins[oldnick]
            self.admins[newnick].nick = newnick

    def is_authed(self, nick):
        authed = []
        printish("called, acquiring condition\n")
        with self.wakeupCond:
            printish("acquired condition")
            p_fn = partial(auth_notify_fn, condition=self.wakeupCond, authed=authed)
            p_fn.__core__ = True
            self.bot.register_callback("NOTICE", p_fn)
            self.bot._msg("NickServ", "ACC %s" % (nick))
            while not authed:
                printish("Not authed yet.")
                self.wakeupCond.wait()
            self.bot.__irccallbacks__["NOTICE"].remove(p_fn)
        return authed[0]

    def init(self, bot):
        bot.auth = self
        self.bot = bot

auth = Authenticator()

__inits__ = [auth.init]
__callbacks__ = {"NICK": [auth.nick]}
