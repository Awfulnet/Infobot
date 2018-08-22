"""
Threads module
"""

import threading
from queue import Queue
import traceback
import logging

def get_core(item):
    if not hasattr(item, "__core__"):
        return False
    return item.__core__

class HandlerThread(threading.Thread):
    def __init__(self, bot, cond: threading.Condition):
        super().__init__()
        self.bot = bot
        self.logger = logging.getLogger("handler-thread")
        self.queue = Queue()

        self.cond = cond

    def run(self):
        self.logger.debug("Calling acquire")
        self.cond.acquire()
        self.cond.notify()
        self.logger.debug("Acquired lock")
        while True:
            try:
                self.handle_commands()
            except (SystemExit,KeyboardInterrupt):
                    traceback.print_exc()

    def handle_commands(self):
        self.logger.debug("Calling wait")
        self.cond.wait()
        self.logger.debug("Wait over")

        items = None
        args = self.queue.get()
        items = self.bot.__irccallbacks__[args[0]]

        self.logger.debug("Calling matching callbacks")
        for item in items:
            if not get_core(item):
                item(self.bot, *(args[1]))

        self.logger.debug("Done")

        self.logger.debug("Calling notify")
        self.cond.notify()

    def push(self, cname, *args):
        self.queue.put(tuple([cname] + list(args)))
