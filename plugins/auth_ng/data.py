from enum import Enum
from dataclasses import dataclass
import re

Action = Enum('Action', ('COMMAND_CALL',))
AuthRes = Enum('AuthRes', ('FAIL', 'CONTINUE', 'SUCCESS'))

@dataclass(frozen=True)
class NUH:
    nick: str
    user: str
    host: str

    @staticmethod
    def from_host(msg):
        ms = re.search("^:?(.+?)!(.+?)@(.+)", msg).groups()
        return NUH(*ms)

    def __repr__(self):
        return "%s!%s@%s" % (self.nick, self.user, self.host)
