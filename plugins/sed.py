import re
import codecs
import string

string.ascii = [chr(i) for i in range(128)]

SUB_REGEX = re.compile(r"^(?:s|(.+?)/s)/((?:\\/|[^/])+)\/((?:\\/|[^/])*?)/([gixs]{0,4})?")

def squeeze(lst, src):
    for ch in lst:
        src = re.sub(ch + r"{2,}", ch, src)
    return src

def sugar(src):
    return src.replace("\\/", "/") \
            .replace("[:upper:]", string.ascii_uppercase) \
            .replace("[:lower:]", string.ascii_lowercase) \
            .replace("[:alpha:]", string.ascii_letters) \
            .replace("[:digit:]", string.digits) \
            .replace("[:xdigit:]", string.hexdigits) \
            .replace("[:alnum:]", string.digits + string.ascii_letters) \
            .replace("[:blank:]", string.whitespace) \
            .replace("[:punct:]", string.punctuation) \
            .replace("[:cntrl:]", "".join([i for i in string.ascii if not i in string.printable])) \
            .replace("[:print:]", string.printable)

def expand(src):
    out = []
    escaped = False
    hyphen = False

    for char in src:
        if char == "\\":
            escaped = True
            continue
        elif char == '-' and not escaped:
            hyphen = True
            escaped = False
            continue
        elif hyphen:
            out.extend(range(out[-1] + 1, ord(char)))
            hyphen = False
        out.append(ord(char))
    return "".join([chr(i) for i in out])


class Substitution(object):
    """ A class representing a substitution in sed. """
    def __init__(self, pattern):
        self.pattern = pattern
        self.qual, self.re, self.sub, self.flags, self.count = self.parse(pattern)
        print("s/%s/%s/%s" % (self.re, self.sub, self.flags))

    def __repr__(self):
        return "Substitution(%r)" % (self.pattern)

    def parse(self, pattern):
        m = SUB_REGEX.match(pattern)
        if not m:
            raise TypeError("Pattern %r isn't a proper substitution pattern!" % (pattern))
        count = 1

        groups = m.groups()
        if 'g' in groups[3]:
            count = 0

        flags = 0
        for c in groups[3]: # for character in flags
            if c != 'g':
                flags += getattr(re, c.upper())

        sub = groups[2].replace("\\/", "/")
        sub = re.sub(r"(?<!\\)(\\)(?=\d+|g<\w+>)", r"\\\\", sub)
        sub = codecs.escape_decode(bytes(sub, "utf-8"))[0].decode('utf-8')

        return list(groups[:-2]) + [sub, flags, count]

    def do(self, on):
        return re.sub(self.re, self.sub, on, count=self.count, flags=self.flags)
