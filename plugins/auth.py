"""
Infobot Authentication Module
"""

from utils.decorators import IRCCallback
from .util.decorators import init

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

	def nick(self, msg):
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
        channel = msg["arg"][1:].strip()

    	if 

	def init(self, bot):
		bot.auth = self


auth = Authenticator()

__inits__ = [auth.init]
__callbacks__ = ["NICK": [auth.nick], "QUIT": [auth.quit],
				 "JOIN": [auth.join], "PART": [auth.part]]
