#!/usr/bin/env python3
from core import DotDict
from core.irc import IRCHandler
from core.threads import HandlerThread
from core.events import Event
from core.events import Standard as StandardEvents
from core.decorators import IRCCallback
from core.style import Styler
from core.plugins import PluginLoader

import json
import threading
import ssl
import logging
import ctypes

try:
    import sdnotify
except ImportError:
    sdnotify = None
    print("sd_notify support missing, not notifying systemd of startup success")

libc = ctypes.CDLL("libc.so.6")

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
        self._send("PRIVMSG {} :{}".format(chan, msg))

    def notice(self, chan, msg):
        self._send("NOTICE {} :{}".format(chan, msg))

    def msg(self, chan, msg):
        msg = str(msg).replace("\r", "")
        if '\n' in msg:
            for item in msg.split("\n"):
                self._msg(chan, item)
        else:
            self._msg(chan, msg)

    @IRCCallback("INVITE")
    def handleinvite(self, pmsg):
        self._send("JOIN :" + pmsg["arg"].split(":")[1])

    def switch(self):
        self.lock.release()
        libc.sched_yield()
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

    @IRCCallback("JOIN")
    def join(self, msg):
        nick = msg["host"].split("!")[0]
        chan = msg["arg"][1:]

        self.events.JoinEvent.fire(self, nick, chan)
        logger.info("[%s] JOIN %s", chan, nick)


    def has_api(self, key):
        return bool(self.config["apis"].get(key, False))

    def gracefully_terminate(self):
        super().gracefully_terminate()


if __name__ == "__main__":
    config = json.load(open("config.json", "r"))
    bot = Infobot(config)
    bot.connect()

    if (sdnotify):
        # Notify systemd that the service startup is complete.
        sdnotify.SystemdNotifier().notify("READY=1")

    bot.run()
