"""
Manages users.
"""

from ..util.decorators import init

from .data import User, Channel, ChannelUserView
from .mode import ModeSet

import logging
import operator
import re

logger = logging.getLogger("ucmgr")

class UserChannelManager:
    def __init__(self, bot):
        self.users = {}
        self.channels = {}
        self.bot = bot

        bot.events.Welcome.register(self._welcome)
        bot.events.Mode.register(self._mode)
        bot.events.Join.register(self._join)
        bot.events.Part.register(self._part)
        bot.events.Kick.register(self._kick)
        bot.events.Quit.register(self._quit)
        bot.events.Names.register(self._names)
        bot.events.NamesEnd.register(self._names_end)
        bot.events.ChannelMode.register(self._channel_mode)

    def _welcome(self, *a, **k):
        self.mode_types = dict(zip(('list', 'param', 'param_set', 'normal'),
                                   self.bot.server_supports.CHANMODES.split(',')))

        modes, prefixes = re.match(r"\(([^)]+)\)(.+)",
                                   self.bot.server_supports.PREFIX).groups()

        self.prefixmodes = dict(zip(prefixes, modes))
        self.modeprefixes = dict(zip(modes, prefixes))

    def _channel_mode(self, bot, channel, modestring, modeargs):
        modes = ModeSet()
        modeargs = iter(modeargs.split())
        for mode in modestring:
            if mode in self.mode_types['param'] \
                    or mode in self.mode_types['param_set']:
                mode_param = next(modeargs)
                modes |= {f"{mode} {mode_param}"}
            else:
                modes |= {mode}

        logger.info(f"Channel {channel} has modes {modes}")
        self.channels[channel].modes = modes


    def _mode(self, bot, user, target, modestring, modeargs):
        logger.info(f"{user} {target} {modestring} {modeargs}", extra={"tag": "hey"})

        args_iter = iter(modeargs)

        mode_action = operator.ior

        if not target.startswith('#'):
            return

        for mode in modestring:
            if mode == '+':
                mode_action = operator.ior
            if mode == '-':
                mode_action = operator.isub

            if mode in self.bot.server_supports['PREFIX'][1:].split(')')[0]:
                user = next(args_iter)
                userobj = self.channels[target].get_user(user)
                user_prev_modes = userobj.modes.copy()
                mode_action(userobj.modes, {mode})
                logger.info(f"User modes for {user} changed from {user_prev_modes} to {userobj.modes}")

    def _join(self, bot, host, chan):
        nick, userhost = host.split('!')
        user, host = userhost.split('@')

        user = self.users.get(nick, User(nick, user, host, self.channels))
        self.users[nick] = user

        channel = self.channels.get(chan, Channel(chan, {}, ModeSet()))
        self.channels[chan] = channel

        channel.add_user(ChannelUserView(user, ModeSet()))
        logger.info(f"{user} joined {channel}")
        pass

    def __repr__(self):
        return f"UCMgr for {len(self.users)} users in {len(self.channels)} channels."

    def _part(self, bot, host, chan, reason):
        username = host.split('!')[0]

        del self.channels[chan].users[username]

        if username == self.bot.config['nick']:
            del self.channels[chan]

        if not self.users[username].channels:
            del self.users[username]

    def _kick(self, bot, kicker, kicked, channel, reason):
        self._part(bot, kicked, channel, reason)

    def _quit(self, bot, host):
        username = host.split('!')[0]
        assert username in self.users
        for channel in self.users[username].channels.values():
            del channel.users[username]
        del self.users[username]

    def map_mode_symbols(self, udesc):
        return ModeSet({*map(self.prefixmodes.get, udesc["modes"])})

    def _names(self, bot, channel_type, channel_name, users):
        logger.debug(f"Got NAMES for {channel_name} (chantype {channel_type})")

        channel = self.channels[channel_name]
        for udesc in users:
            modes = self.map_mode_symbols(udesc)
            del udesc["modes"]

            user = self.users.get(udesc["nick"], User(**udesc, all_channels=self.channels))

            self.users[user.nick] = user
            chanuser = channel.users.get(udesc["nick"], False)
            if chanuser:
                chanuser.modes = modes
                chanuser.user.update_from_dict(udesc)
            else:
                chanuser = ChannelUserView(user, modes)
                channel.add_user(chanuser)

    def _names_end(self, bot, channel_name):
        channel = self.channels[channel_name]
        logger.info(f"Successfully joined {channel}")


@init
def plugin_init(bot):
    bot.ucmgr = UserChannelManager(bot)
