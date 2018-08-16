from .mode import ModeSet
from dataclasses import dataclass


@dataclass
class User:
    nick: str
    user: str
    host: str
    all_channels: dict

    def __repr__(self):
        return f"{self.nick}!{self.user}@{self.host}"

    def update_from_dict(self, user):
        self.nick = user["nick"]
        self.user = user["user"]
        self.host = user["host"]

    @property
    def channels(self):
        return {name:channel for name,channel in self.all_channels.items()
                if self in channel}

class ChannelUserView:
    def __init__(self, user, modes=None):
        self.user = user

        if isinstance(modes, str):
            modes = ModeSet(modes)

        self.modes = modes or ModeSet()

    def __getattr__(self, name):
        """ Allow people to use the User attribute on CUV """
        return getattr(self.user, name)

    def __repr__(self):
        return f"{self.user} ({self.modes})"

@dataclass
class Channel:
    name: str
    users: dict
    modes: ModeSet

    @property
    def is_pm(self):
        return not self.name.startswith('#')

    def __repr__(self):
        return f"{self.name} ({self.modes}) ({len(self.users)} users)"

    def add_user(self, user: ChannelUserView):
        if not isinstance(user, ChannelUserView):
            raise TypeError("User is not a ChannelUserView!")
        self.users[user.nick] = user

    def get_user(self, nick):
        return self.users[nick]

    def __contains__(self, user):
        if isinstance(user, User):
            return user.nick in self.users
        return user in self.users
