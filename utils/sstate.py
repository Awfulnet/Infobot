"""
ServerState, Channel and ChannelHandler objects.
"""

from .channel import Channel, UserDict

class FancySet(set):
    def replace(self, o, n):
        self.discard(o)
        self.add(n)

class DotDict(dict):
    def __getattribute__(self, name):
        if name != "keys":
            if name in self.keys():
                return self[name]
        return super().__getattribute__(name)

class ChannelHandler(dict):
    """ A class that handles channels. """
    def add(self, channel):
        if type(channel) == str:
            self.update({channel: Channel(channel)})
        elif type(channel) == Channel:
            if channel in self.values():
                self.update_channel(self[channel.name], channel)
            self.update({channel.name: channel})
        else:
            raise TypeError("Type of argument passed to %s.add should be Channel or str"
                % (str(self)))

    def __str__(self):
        return "ChannelHandler"

    def get_channels_for(self, user):
        assert user == user.lower()
        channels_ = ChannelHandler()
        for v in self.values():
            if user in v.users.keys():
                channels_.add(v)
        return channels_

    def update_channel(self, *args):
        to_merge = args[0]
        merge_with = args[1]
        to_merge.users |= merge_with.users

    def __getattribute__(self, name):
        if name != "keys":
            if "#"+name in self.keys():
                return self["#"+name]
        if name in dir(ChannelHandler):
            return super().__getattribute__(name)
        raise AttributeError("'%s' object has no attribute '%s', have you joined '#%s'?"
            % (self, name, name))

class ServerState(object):
    """ A class that holds the active channels and admins and some more things about the bot that are server-specific. """
    def __init__(self, bot):
        self.bot = bot
        self.admins = FancySet()
        self.muted = FancySet()
        self.nick = "James"
        self.notices = []
        self.messages = {}
        self.channels = ChannelHandler()
        self.users = UserDict(bot)
        self.events = DotDict()

    def add_admin(self, nick):
        """ Add an user to the admin list. """
        self.admins.add(nick.lower())

    def del_admin(self, dnick):
        """ Remove an user from the admin list. """
        self.admins.remove(dnick.lower())

    def mute(self, nick):
        """ Add an user to the mute list. """
        self.muted.add(nick.lower())

    def unmute(self, dnick):
        """ Remove an user from the block list. """
        self.muted.remove(dnick.lower())
