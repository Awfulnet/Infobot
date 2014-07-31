""" 
Do channel STUFF
"""

import sys
from subprocess import Popen
import time
from datetime import datetime

bot = None

class User(object):
    def __init__(self, nick, channels=None):
        self.nick = nick
        self.exactnick = ""

    @property
    def channels(self):
        return bot.state.channels.get_channels_for(self.nick)

    @property
    def messages(self):
        return bot.state.messages[self.nick]

    def __repr__(self):
        return "User(nick=%r, channels=%s)" % (self.nick, self.channels.keys())

    def kick(self, channel):
        bot._send("KICK %s %s :Requested" % (channel, self.nick))

class UserDict(dict):
    """ A dictionary with users """
    def __init__(self, bot_server=None):
        if bot_server:
            global bot
            bot = bot_server

    def get(self, *args, **kwargs):
        args = list(args)
        try:
            args[0] = args[0].lower()
        except AttributeError:
            raise TypeError("Argument 0 should be of type str, not %s" % (type(args[0])))
        return super().get(*args, **kwargs)

    def __str__(self):
        return "UserDict"

    def discard(self, item):
        try:
            del self[item]
        except KeyError:
            pass

    def __setitem__(self, item, value):
        super().__setitem__(item, value)

    def __getattribute__(self, item):
        if item != "keys":
            if item in self.keys():
                return self[item]
        if item in dir(UserDict):
            return super().__getattribute__(item)
        else:
            raise AttributeError("'%s' object has no attribute '%s', is '%s' in the channel?"
                % (self, item, item))

class Channel(object):
    # TODO: ADD KICK STUFF
    def __init__(self, name):
        self.name = name
        self.disabled_commands = set()
        self.users = UserDict()
        self.state = bot.state

    def add_user(self, user):
        assert user == user.lower(), "User is passed as lowercase."
        existing_user = self.state.users.get(user, False)
        if existing_user:
            self.users[user] = existing_user
        else:
            self.state.users[user] = User(user)
            self.users[user] = self.state.users[user]

    def remove_user(self, user):
        del self.users[user.lower()]

    def change_user(self, map_):
        uobj = self.users[map_[0]]
        uobj.nick = map_[1]
        self.users.discard(map_[0])
        self.users[map_[1]] = uobj
        return self.users[map_[1]]

    def update_users(self, update):
        update = [u.lower() for u in update]
        for user in update:
            existing_user = self.state.users.get(user, False)
            if existing_user:
                self.users[user] = existing_user
            else:
                self.state.users[user] = User(user)
                self.users[user] = self.state.users.get(user)
        return self.users

    def __repr__(self):
        return "Channel(name=%r)" % (self.name)

    def __call__(self):
        return self.name