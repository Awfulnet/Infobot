"""
Infobot Authentication Module
"""

from utils.decorators import IRCCallback
from .util.decorators import init
from utils import now

import re

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

    def isadmin(self, person):
        return True if person.nick in self.admins and self.admins[person.nick].host == person.host else False

    def addadmin(self, person):
        self.admins[person.nick] = person

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

    def join(self, msg):
        nick = msg["host"].split("!")[0].strip()
        user = User.from_host(msg["host"])
        channel = msg["arg"][1:].strip()

        print("[main thread:%s] JOIN %s %s" % (now(), nick, channel))

    def init(self, bot):
        bot.auth = self

setattr(Authenticator.join, "__core__", True)
auth = Authenticator()

__inits__ = [auth.init]
__callbacks__ = {"NICK": [auth.nick],
                 "JOIN": [auth.join]}
