#!/usr/bin/env python3
from utils.irc import IRCHandler
from utils.threads import HandlerThread
from utils.events import Event
from utils.events import Standard as StandardEvents
from utils.sstate import DotDict
from utils.decorators import IRCCallback
from utils import now

import re
import traceback
import sys
import json
import threading
import datetime
import time

import plugins
from plugins.auth import User

VERSION = "1.0.0"

class Infobot(IRCHandler):
    """ Infobot main class """
    def __init__(self, config):
        print("Infobot version %s" % (VERSION))
        super().__init__(config, verbose=False)

        self.config = config
        self.nick = config["nick"]

        # Arbitrary bot data
        self.data = {}
        self.auth = None

        self.lock = threading.Lock()
        self.lock.acquire()

        self.events = DotDict({list(i.keys())[0]: Event(list(i.values())[0])
            for i in StandardEvents})

        self.cmd_thread = HandlerThread(self, self.lock)
        self.cmd_thread.daemon = True
        self.register_callbacks()
        self.register_plugins(plugins.get_plugins())

        self.auth.addadmin(User("svkampen", "svkampen", "38485360.F44253B8.A42ECE66.IP"))

    def __repr__(self):
        return "Infobot(server=%r)" % (self.config["server"].split(':')[0])

    def register_callback(self, ctype, func):
        if ctype in self.__irccallbacks__:
            self.__irccallbacks__[ctype].append(func)
        else:
            self.__irccallbacks__[ctype] = [func]

    def _msg(self, chan, msg):
        self.sock.send(b"PRIVMSG ")
        self.sock.send(("%s :%s" % (chan, msg)).encode('utf-8'))
        self.sock.send(b"\r\n")

    def notice(self, chan, msg):
        self.sock.send(b"NOTICE ")
        self.sock.send(("%s :%s" % (chan, msg)).encode('utf-8'))
        self.sock.send(b"\r\n")

    def msg(self, chan, msg):
        msg = str(msg).replace("\r", "")
        if '\n' in msg:
            for item in msg.split("\n"):
                self._msg(chan, item)
        else:
            self._msg(chan, msg)

    @IRCCallback("INVITE")
    def handleinvite(self, pmsg):
        bot._send("JOIN :" + pmsg["arg"].split(":")[1])

    def switch(self):
        self.lock.release()
        time.sleep(0.01)
        self.lock.acquire()

    @IRCCallback("MODE")
    def mode(self, msg):
        """ Handle MODE. """
        if not msg["arg"].startswith("#"):
            self.nick = msg["arg"].split(" ", 1)[0]

    def connect(self):
        self.cmd_thread.start()
        super().connect()

    def msg(self, chan, msg):
        """ Send a message to a channel. """
        self._msg(chan, msg)

    @IRCCallback("PRIVMSG")
    def privmsg(self, msg):
        """ Handles messages. """
        nick = msg["host"].split('!')[0]
        chan = msg["arg"].split()[0]
        chan = chan.lower()
        if not chan.startswith("#"):
            # Private message. File under sender.
            chan = nick
        msg = msg["arg"].split(":", 1)[1]

        self.events.MessageEvent.fire(self, nick, chan, msg)
        print("[main thread:%s] [%s] <%s> %s" % (now(), chan, nick, msg))

    def register_plugins(self, plugins):
        for plugin in plugins:
            print("[main thread:%s] processing plugin %s" % (now(), plugin.__file__))
            if hasattr(plugin, "__callbacks__"):
                for k, v in plugin.__callbacks__.items():
                    for i in v:
                        try:
                            self.__irccallbacks__[k].append(i)
                        except KeyError:
                            self.__irccallbacks__[k] = [i]
            if hasattr(plugin, "__inits__"):
                for init in plugin.__inits__:
                    init(self)

    @IRCCallback("376", "422")
    def welcome(self, msg):
        if self.config.get("ident_pass", None):
            self._msg(self.config["ident_service"], "identify %s"
                % (self.config["ident_pass"]))
        self._send("MODE %s +B" % (self.nick))

        for channel in self.config["autojoin"]:
            self._send("JOIN :%s" % (channel))

    def gracefully_terminate(self):
        super().gracefully_terminate()


if __name__ == "__main__":
    config = json.loads(open("config.json", "r").read())
    bot = Infobot(config)
    bot.connect()
