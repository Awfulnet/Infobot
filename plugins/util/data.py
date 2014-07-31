www_headers = {
    "User-Agent": "Mozilla/5.0 (compatible) (Python 3.3, en_US) James/5.0 IRC bot"
}

import inspect
import random
import gc
from types import FunctionType
import math
import re

def sugar(arg):
    arg = arg.replace("ssalc", "")
    arg = arg.replace("fed", "")
    arg = arg.replace("self", "bot")
    return arg

def split_on(s, n):
    part = s[:n]
    part2 = s[n+1:]
    return part, part2

def lineify(data, max_size=400):
    """ Split text up into IRC-safe lines. """
    if len(data) < max_size:
        return [data]
    if not ' ' in data:
        return re.findall(r".{0,%d}", data)
    
    lines = []
    while len(data) > max_size:
        spaceplace = data.rfind(" ", 0, max_size)
        part, data = split_on(data, spaceplace)
        lines.append(part)
    lines.append(data)
    return lines



def get_doc():
    frame = inspect.getouterframes(inspect.currentframe())[1][0]
    code_obj = frame.f_code
    funcname = inspect.getframeinfo(frame).function
    referrers = [obj for obj in gc.get_referrers(code_obj) if isinstance(obj, FunctionType)]
    referrer = [obj for obj in referrers if obj.__name__ == funcname][0]
    return referrer.__doc__



def generate_vulgarity():
    swears = ["FUCK", "SHIT", "DICK", "TWAT", "CUNT", "FISH", "CRAP", "ASS", "TIT", "PUSSY", "COCK", "DOUCHE", "CUM", "PISS", "MAN", "CRUD"]
    nouns = ["STAIN", "BAG", "FUCKER", "TARD", "WAFFLE", "NIPPLE", "BOOB", "BURGER", "EATER", "HOLE", "PONY", "NUTS", "JUICE", "CHODE", "SLUT", "BREATH", "WHORE", "DONKEY", "GOBBLER", "NUGGET", "BRAIN", "MUNCHER", "SUCKER", "STICK", "FACE", "TOOL", "WAGON", "WAD", "BUTT", "BUCKET", "BOX"]
    swearnoun = ["DIPSHIT", "FUCKWIT", "DUMBASS", "CORNHOLE", "LIMPDICK", "PIGSHIT"]
    if random.random() < 0.05:
        vulgarity = random.choice(swearnoun)
    else:
        vulgarity = random.choice(swears) + random.choice(nouns)

    return vulgarity