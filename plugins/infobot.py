from .util.decorators import command, init
from .database import Database

db = None

@init
def init(bot):
	global db
	db = Database(password=bot.config["dbpass"])

@command('sql', '&$name .+', admin=True)
def execsql(bot, nick, chan, arg):
	db.execute(arg)
	bot._msg(chan, "%s" % (db.fetchall()))