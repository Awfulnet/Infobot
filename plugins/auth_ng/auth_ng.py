"""
Infobot auth-ng
"""

from collections import defaultdict
from . import tags
from .tags import Tag
from .data import NUH, Action, AuthRes, TagTypeError
from ..util.decorators import init
from typing import List

import logging
logger = logging.getLogger("auth-ng")

class Authenticator:
    def __init__(self, bot):
        self.bot = bot

        self._user_tags = defaultdict(list)
        for nuh, taglst in bot.config["user_tags"].items():
            user = NUH.from_host(nuh)
            for tag in taglst.split(','):
                self.add_tag(user, tag)

        logger.info(f"Set up tags: {self._user_tags}")

    def add_tag(self, nuh: NUH, tagdesc: str):
        type, *args = tagdesc.split(':')
        if not hasattr(tags, type.title()):
            raise TagTypeError(f"Invalid tag type: {type}")
        tag = getattr(tags, type.title())(*args)
        self._user_tags[nuh].append(tag)

    def rm_tag(self, nuh: NUH, tagdesc: str):
        new_tags = self._user_tags[nuh]
        for tag in self._user_tags[nuh]:
            if repr(tag) == tagdesc:
                new_tags.remove(tag)
        self._user_tags[nuh] = new_tags

    def tags_for_nick(self, nick: str) -> List[Tag]:
        for nuh, taglst in self._user_tags.items():
            if nuh.nick == nick:
                return taglst
        return []

    def try_auth(self, action: Action, data, host) -> AuthRes:
        user = NUH.from_host(host)
        taglst = self._user_tags.get(user, [])
        for tag in taglst:
            authres = tag.try_auth(self.bot, action, data, user)

            if authres == AuthRes.SUCCESS:
                return AuthRes.SUCCESS
            if authres == AuthRes.CONTINUE:
                continue
            if authres == AuthRes.FAIL:
                return AuthRes.FAIL

        return AuthRes.FAIL

@init
def plugin_init(bot):
    bot.authmgr = Authenticator(bot)
