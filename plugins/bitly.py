"""
Bit.ly plugin for James
"""
import requests
import re
from .util.decorators import command, init
from .util.data import get_doc

URL_REGEX = re.compile(r'(?:(?:https?|ftp)://)(?:\S+(?::\S*)?@)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:/[^\s]*)?', re.I)

def _shorten(bot, url):
    """ Shorten an url with bit.ly """
    login = bot.config["apis"]["bit.ly"]["user"]
    key = bot.config["apis"]["bit.ly"]["key"]

    surl = "https://api-ssl.bitly.com/v3/shorten"
    page = requests.get(surl, params={"login": login,
                                      "apiKey": key,
                                      "longurl": url})

    return page.json()["data"]["url"]

def urlfinder(bot, nick, chan, msg):
    urls = URL_REGEX.findall(msg)
    for url in urls:
        bot.data["urlhistory"].append(url)
    if not urls:
        return
    print(urls)
    short_urls = [_shorten(bot,url) for url in urls if len(url) > 90]
    short_urls = ["%s %s" % (bot.style.grey("(%d)" % i), bot.style.lblue(url))
            for i, url in enumerate(short_urls)]
    separator = bot.style.grey(", ")
    output = separator.join(short_urls)

    bot.notice(chan, output)

@command('shorten', r'^(!|.)$name(?:$|\s\d+)')
def shorten(bot, nick, chan, gr, arg):
    """ {!.}shorten [url|number] -> Shorten a URL """
    if gr[0] == '.':
        msgfn = bot.notice
    else:
        msgfn = bot._msg

    if not arg:
        if len(bot.data["urlhistory"]) >= 1:
            return msgfn(chan,
                    bot.style.lblue(_shorten(bot, bot.data["urlhistory"][-1])))
        else:
            return

    n = int(arg)
    if len(bot.data["urlhistory"]) < n:
        return msgfn(chan, bot.style.red("Error: n > URL history length"))
    return msgfn(chan,
            bot.style.lblue(_shorten(bot, bot.data["urlhistory"][-n])))

@command('shorten', r'^(!|.)$name\s' + URL_REGEX.pattern + '$')
def shorten_url(bot, nick, chan, gr, arg):
    """ {!.}shorten [url|number] -> Shorten a URL """
    if gr[0] == '.':
        msgfn = bot.notice
    else:
        msgfn = bot._msg

    return msgfn(chan,
            bot.style.lblue(_shorten(bot, arg)))


@init
def plugin_initializer(bot):
    """ Initialize this plugin. """
    if (bot.has_api("bit.ly")):
        bot.data["urlhistory"] = []
        bot.events.MessageEvent.register(urlfinder)
