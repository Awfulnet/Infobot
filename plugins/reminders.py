"""
.tell and .remind from Karkat, Infobot-ized

* depends: database
"""
import parsedatetime
import humanize
import regex
import threading
import logging

from pytz import timezone
from .util.decorators import command, init, process_privmsg
from .util.dict import CaseInsensitiveDefaultDict as CIDD
from .util.data import CommandException
from collections import namedtuple
from datetime import datetime

logger = logging.getLogger("remind")
logger.setLevel(logging.DEBUG)

db = None
Tell = namedtuple("Tell", ["id", "from_nick", "message", "date"])
Reminder = namedtuple("Reminder", ["id", "to_nick", "from_nick", "message", "channel", "begints", "endts"])

calendar = parsedatetime.Calendar()

timers = []
reminders = CIDD(default=[])
tells = CIDD(default=[])

REMIND_RE = "\.remind (me|@?[A-z0-9]+) (?:in (.+?) to (.+)$|(?:to )?(.+?) in (.+)$)"

REMIND_TELL_RE = regex.compile(r"""^
    \.(?:tell|remind)\s
        (?P<nick> me|@? [A-z0-9]+)\s
        (?:
            (?:in\s(?P<time> .+?))\s(?:to \s (?P<message>.+)$)
            |
            (?:
                (?:to \s )?
                    (?:(?P<message>.+)\sin\s(?P<time>.+)
                    |
                    (?P<message>.+)
                )
            )
        )""",
        regex.X | regex.V1)

def add_tell(to_nick, tellid, from_nick, message, begints):
    tells[to_nick].append(
        Tell(tellid, from_nick, message, begints))

def add_reminder(bot, *args):
    reminder = Reminder(*args)
    current_time = datetime.utcnow()
    if (current_time >= reminder.endts):
        remind_handler(bot, reminder)
        return

    delta = reminder.endts - datetime.utcnow()
    timer = threading.Timer(delta.total_seconds(), remind_handler, args=(bot, reminder))
    timer.reminder = reminder
    timer.start()
    timers.append(timer)
    reminders[reminder.to_nick].append(reminder)
    logger.debug("Added reminder %r (fires in %f seconds)", reminder, delta.total_seconds())

def db_get_tells():
    data = db.execute("SELECT to_nick, tellid, from_nick, message, begints FROM tells WHERE fulfilled = false;").fetchall()
    for tell in data:
        add_tell(*tell)

def db_get_reminders(bot):
    data = db.execute("SELECT id, to_nick, from_nick, message, channel, begints, endts FROM reminders WHERE fulfilled = false;").fetchall()
    for reminder in data:
        add_reminder(bot, *reminder)

def send_tell(bot, nick, chan, tell):
    timestring = humanize.naturaltime(datetime.utcnow() - tell.date)

    output = "{} {}: {} · {} · {}".format( # message indicator, to_nick, message, from, time
        bot.style.green("| ✉ |"),
        bot.style.teal(nick),
        bot.style.teal(tell.message),
        bot.style.teal("from {}".format(tell.from_nick)),
        bot.style.teal("\u231A {}".format(timestring))
    )
    bot.notice(chan, output)

    db.execute("UPDATE tells SET fulfilled = true WHERE tellid = %s;", (tell.id))

def tell_handler(bot, nick, chan):
    if nick in tells:
        for tell in tells[nick]:
            send_tell(bot, nick, chan, tell)
        del tells[nick]

def remind_handler(bot, reminder, late_time=None):
    timestring = humanize.naturaltime(datetime.utcnow() - reminder.begints)
    output = "{} {}: {} · {} · {}".format(
        bot.style.green("| ✉ |"),
        bot.style.teal(reminder.to_nick),
        bot.style.teal(reminder.message),
        bot.style.teal("from {}".format(reminder.from_nick)),
        bot.style.teal("\u231A {}".format(timestring))
    )

    bot.notice(reminder.channel, output)

    db.execute("UPDATE reminders SET fulfilled = true WHERE id = %s;", (reminder.id,))

__callbacks__ = {
    "PRIVMSG": [
        lambda b,m: tell_handler(b, *process_privmsg(m)[:2])
    ]}

@command('remind', REMIND_TELL_RE)
def remind(bot, nick, chan, gr, arg):
    to_nick = gr['nick']
    time = gr['time']
    message = gr['message']
    if (to_nick == 'me'):
        to_nick = nick

    pronoun = 'them' if to_nick != nick else "you"

    to_nick = to_nick.strip('@')

    if (time is not None):
        # this is a reminder, as it has an end time
        endts = calendar.parseDT(time, tzinfo=timezone("UTC"))[0]
        # UTCnow doesn't add a timezone attribute, so we have to add it ourselves
        utcnow = datetime.utcnow().replace(tzinfo=timezone("UTC"))
        delta = endts - utcnow

        reminderid = db.execute("INSERT INTO reminders (from_nick, to_nick, message, channel, endts) VALUES (%s,%s,%s,%s,%s) RETURNING id;",
                                (nick, to_nick, message, chan, endts)).fetchone()[0]

        add_reminder(bot, reminderid, to_nick, nick, message, chan, utcnow, endts)

        bot.msg(chan, f"I'll remind {pronoun} in {delta}. To cancel, send .rmcancel {reminderid}.")
    else:
        # this is a tell
        tellid = db.execute("INSERT INTO tells (to_nick, from_nick, message) VALUES (%s,%s,%s) RETURNING tellid;",
                (to_nick, nick, message)).fetchone()[0];

        tells[to_nick].append(Tell(tellid, nick, message, datetime.utcnow()))

        bot.msg(chan, f"I'll tell {pronoun} that. To cancel, send .tcancel {tellid}.")

@command('rmcancel', cmdchar='.')
def cancel_reminder(bot, nick, chan, arg):
    """ .rmcancel <id> - Cancels your started reminder, if possible. """
    try:
        rid = int(arg)
    except ValueError:
        raise CommandException(f"reminder id missing or invalid.", send_doc=True)

    row = db.execute("SELECT from_nick, to_nick, message, endts FROM reminders WHERE id = %s;",
                     (rid,)).fetchone()

    if not row:
        raise CommandException("that reminder does not exist.")

    from_nick, to_nick, message, endts = row

    if endts <= datetime.utcnow():
        raise CommandException("that reminder has already fired.")

    if from_nick != nick:
        raise CommandException("you did not create that reminder!")

    db.execute("DELETE FROM reminders WHERE id = %s;", (rid,))
    for timer in timers:
        if timer.reminder.id == rid:
            timer.cancel()
            break

    bot.msg(chan, "Reminder cancelled successfully.")

@command('tcancel', cmdchar='.')
def cancel_tell(bot, nick, chan, arg):
    """ .tcancel <id> - Cancels your tell, if possible. """
    try:
        tid = int(arg)
    except ValueError:
        raise CommandException(f"tell id missing or invalid.", send_doc=True)

    row = db.execute("SELECT to_nick, from_nick, message, begints, fulfilled FROM tells WHERE tellid = %s;",
                     (tid,)).fetchone()

    if not row:
        raise CommandException("that tell does not exist.")

    to_nick, from_nick, message, begints, fulfilled = row

    if fulfilled:
        raise CommandException("that tell has already been sent.")

    if from_nick != nick:
        raise CommandException("you did not create that tell!")

    db.execute("DELETE FROM tells WHERE tellid = %s;", (tid,))
    for tell in tells[to_nick]:
        if tell.id == tid:
            to_remove = tell
            break

    tells[to_nick].remove(to_remove)
    bot.msg(chan, "Tell cancelled successfully.")


@init
def init(bot):
    global db
    db = bot.data["db"]
    db_get_tells()
    bot.events.Welcome.register(lambda: db_get_reminders(bot))

    bot.events.Join.register(lambda bot, host, channel: tell_handler(bot, host.split('!')[0], channel))
