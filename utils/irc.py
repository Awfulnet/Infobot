"""
IRC API - irc.py
"""

import sys
from .buffer import Buffer
from . import parse
import socket
from .num import NUM as numerics
import time
import traceback
import types
import inspect
from . import now

CONFIG = {}

class IRCHandler(object):
    """ IRCHandler(Dict<string, object> config) - a standard IRC handler """
    def __init__(self, bconfig, verbose=False):
        globals()["CONFIG"] = bconfig
        self.sock = socket.socket()
        self.sock_file = None
        self.verbose = verbose
        self.running = True
        self.buff = Buffer()
        self.outbuff = Buffer()
        self.is_welcome = False

    def connect(self):
        """ Connect to the IRC server and start the main loop """
        server = CONFIG["server"].split("|")[0].split(":")
        self.sock.connect((server[0], int(server[1])))
        try:
            passwd = CONFIG["server"].split("|", 1)[1]
            if passwd:
                self._send("PASS "+passwd)
        except:
            pass
        self.mainloop()

    def mainloop(self):
        """ The main loop. """
        loops = 0
        try:
            while self.running:
                if loops != 0:
                    try:
                        self.buff.append(self.sock_file.readline().decode('utf-8', errors='ignore'))
                    except UnicodeDecodeError:
                        traceback.print_exc()
                else:
                    self.sock_file = self.sock.makefile('rb')
                    self.sendnick()
                    self.senduser()

                for msg in self.buff:
                    if self.verbose:
                        print(">>> "+msg)
                    pmsg = parse.parse(msg)
                    if pmsg["method"] == "PING":
                        self._send("PONG "+pmsg["arg"])
                    elif pmsg["method"] in ("376", "422"):
                        self.is_welcome = True
                        self.run_callback(pmsg["method"], pmsg)
                    else:
                        #print(pmsg["method"])
                        self.run_callback(pmsg["method"], pmsg)
                loops += 1
        except KeyboardInterrupt:
            sys.exit()

    def _send(self, data, newline="\r\n", sock=None):
        """ Send data through the socket and append CRLF. """
        self.outbuff.append(data+newline)
        for msg in self.outbuff:
            if self.verbose:
                print("<<< "+msg)
            self.sock.send((msg+newline).encode("utf-8"))
            time.sleep(.01)

    def run_callback(self, cname, *args):
        noncore = False
        funcs = self.__irccallbacks__.get(cname, None)
        __core__ = None
        if not funcs:
            return
        for func in funcs:
            if not hasattr(func, "__core__"):
                __core__ = False
            else:
                __core__ = getattr(func, "__core__")
            if __core__:
                if type(func) == types.MethodType:
                    func(*args)
                else:
                    func(self, *args)
            else:
                noncore = True
        if noncore:
            self.cmd_thread.push(cname, args)
            self.switch()

    def senduser(self):
        """ Send the IRC USER message. """
        self._send("USER %s * * :%s" % (CONFIG["nick"], CONFIG["real"]))

    def sendnick(self):
        """ Send the IRC NICK message. """
        self._send("NICK %s" % (CONFIG["nick"]))

    def register_callbacks(self):
        self.__irccallbacks__ = {}
        funcs = list(dict(inspect.getmembers(self, predicate=inspect.ismethod)).values())
        for func in funcs:
            if "return" in func.__annotations__:
                for item in func.__annotations__["return"]:
                    print("[main thread:%s] registering %s for %s" % (now(), func, item))
                    if item in self.__irccallbacks__:
                        self.__irccallbacks__[item].append(func)
                    else:
                        self.__irccallbacks__[item] = [func]

    def gracefully_terminate(self):
        """ Gracefully terminate the bot. """
        self.running = False
