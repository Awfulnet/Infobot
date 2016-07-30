#!/usr/bin/env python3
from utils.irc import IRCHandler
from utils.threads import HandlerThread
from utils.events import Event
from utils.events import Standard as StandardEvents
from utils.sstate import DotDict
from utils.decorators import IRCCallback
from utils.style import Styler
from utils.plugins import PluginLoader

import re
import traceback
import json
import threading
import datetime
import time
import ssl
import sys
import logging

VERSION = "1.1.0"

LOGLEVEL = logging.DEBUG
FORMAT = "[%(asctime)s] [%(levelname)7s] %(name)7s: %(message)s"
logging.basicConfig(filename="infobot.log", level=LOGLEVEL)
logger = logging.getLogger("infobot")

import coloredlogs

class Infobot(IRCHandler):
    """ Infobot main class """
    def __init__(self, config):
        self.register_logger()

        logger.info("Infobot version %s", VERSION)
        logger.info("© 2014-2016 Sam van Kampen, Simmo Saan and contributors")
        super().__init__(config, verbose=False)

        self.style = Styler()
        self.config = config
        self.nick = config["nick"]

        # Arbitrary bot data
        self.data = {"topics": {}}
        self.auth = None

        self.lock = threading.Lock()
        self.lock.acquire()

        self.events = DotDict({list(i.keys())[0]: Event(list(i.values())[0])
            for i in StandardEvents})

        self.cmd_thread = HandlerThread(self, self.lock)
        self.cmd_thread.daemon = True
        self.register_callbacks()
        self.register_plugins()

        for item in self.config["admins"]:
            self.auth.addadmin(item[0], item[1], item[2])

    def __repr__(self):
        return "Infobot(server=%r)" % (self.config["server"].split(':')[0])

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
        if self.config["ssl"]:
            self.sock = ssl.wrap_socket(self.sock)
        super().connect()
        self._send("NICK %s" % (bot.config["nick"]))

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
        logger.info("[%s] <%s> %s" , chan, nick, msg)

    @IRCCallback("NOTICE")
    def notice_listener(self, msg):
        logger.info("*%s* %s", msg["host"], msg["arg"].split(" ", 1)[1][1:])

    def register_logger(self):
        root = logging.getLogger()

        sh = logging.StreamHandler()
        sh.setLevel(LOGLEVEL)

        formatter = coloredlogs.ColoredFormatter(fmt=FORMAT, field_styles={
            "hostname": {"color": "blue"},
            "programname": {"color": "cyan"},
            "name": {"color": "red"},
            "levelname": {"color": "magenta"},
            "asctime": {"color": "cyan"}
        })
        sh.setFormatter(formatter)
        root.addHandler(sh)

    def register_plugins(self):
        pluginLoader = PluginLoader()
        plugins = pluginLoader.load_all()
        for plugin in plugins:
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
        logger.info("Loaded %d plugins (%s)", len(plugins), ' ⇒ '.join(plugin.__name__.rsplit('.',1)[1] for plugin in plugins))


    @IRCCallback("332") # RPL_TOPIC
    def topicget(self, msg):
        chan = msg["arg"].split()[1]
        chan = chan.lower()
        arg = msg["arg"].split(':', 1)[1]
        self.data["topics"][chan] = arg

    @IRCCallback("376", "422")
    def welcome(self, msg):
        if self.config.get("ident_pass", None):
            self._msg(self.config["ident_service"], "identify %s"
                % (self.config["ident_pass"]))
        self._send("MODE %s +B" % (self.nick))

        for channel in self.config["autojoin"]:
            self._send("JOIN :%s" % (channel))

    def has_api(self, key):
        return bool(self.config["apis"].get(key, False))

    def gracefully_terminate(self):
        super().gracefully_terminate()


if __name__ == "__main__":
    config = json.load(open("config.json", "r"))
    bot = Infobot(config)
    bot.connect()
