"""
.tell and .remind from Karkat, Infobot-ized

* depends: database
"""
import parsedatetime
import datetime
import humanize

from .util.decorators import command, init, process_privmsg
from collections import namedtuple, defaultdict

db = None
Tell = namedtuple("Tell", ["id", "from_nick", "message", "date", "fulfilled"])

tells = defaultdict(list)

@init
def init(bot):
    global db
    db = bot.data["db"]
    data = db.execute("SELECT to_nick, tellid, from_nick, message, begints FROM tells WHERE fulfilled = false;").fetchall()
    for tell in data:
        tells[tell[0]].append(Tell(tell[1], tell[2], tell[3], tell[4], False))

def tell_handler(bot, pmsg):
    nick, chan, msg = process_privmsg(pmsg)

    if nick in tells:
        for tell in tells[nick]:
            send_tell(bot, nick, chan, tell)
            fulfill_db(tell.id)
        del tells[nick]

__callbacks__ = {"PRIVMSG": [tell_handler]}

@command('tell', r'^\.tell .+')
def tell(bot, nick, chan, arg):
    """ .tell <nick> <message> - Tells <nick> your message when they are next seen """
    args = arg.split(" ",1)
    db = bot.data["db"]
    if len(args) < 2:
        return bot._msg(chan, get_doc())

    to_nick, message = args
    date = datetime.datetime.utcnow()

    tellid = db.execute("INSERT INTO tells (to_nick, from_nick, message) VALUES (%s,%s,%s) RETURNING tellid;",
               (to_nick, nick, message)).fetchone()[0];

    tells[to_nick].append(Tell(tellid, nick, message, date, False))
    bot.msg(chan, "I'll tell them that.")

def send_tell(bot, nick, chan, tell):
    timestring = humanize.naturaltime(datetime.datetime.utcnow() - tell.date)

    output = "{} {}: {} · {} · {}".format( # message indicator, to_nick, message, from, time
        bot.style.green("| ✉ |"),
        bot.style.teal(nick),
        bot.style.teal(tell.message),
        bot.style.teal("from {}".format(tell.from_nick)),
        bot.style.teal("\u231A {}".format(timestring))
    )
    bot.notice(chan, output)

def fulfill_db(tellid):
    db.execute("UPDATE tells SET fulfilled = true WHERE tellid = %s;", (tellid))

