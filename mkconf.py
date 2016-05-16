#!/usr/bin/env python3

import json
import os
import re

from pprint import pformat as pprint

c = {}
cfile = open("config.json", "w+")

print("mkconf.py, version 1.0")

c["server"] = input("Server (host:port|password): ")
c["nick"] = input("Nickname (default: Infobot): ") or 'Infobot'
c["realname"] = input("Real name (default: Subluminal/Infobot): ") or "Subluminal/Infobot"
admins = input("Admins (nick!user@host, comma separated): ").split(',')
c["admins"] = [[x[0], x[1], x[2]] for x in [re.split("!|@", i) for i in admins]]

c["autojoin"] = input("Autojoin (#channel, comma separated): ").split(',')
c["dbhost"] = input("Database host (default: localhost): ") or 'localhost'
c["dbpass"] = input("Database password: ")
c["ident_service"] = input("Ident service (default: NickServ): ") or "NickServ"
c["ident_pass"] = input("Ident service pass: ")
c["ssl"] = input("Use SSL? y/N: ")

if c["ssl"] == "y":
    c["ssl"] = True
else:
    c["ssl"] = False

bitlysupport = input("Enable bit.ly shortening support? y/N: ")
if bitlysupport == 'y':
    c["apis"] = {}
    c["apis"]["bit.ly"] = {}
    c["apis"]["bit.ly"]["user"] = input("Bit.ly username: ")
    c["apis"]["bit.ly"]["key"] = input("Bit.ly key: ")

json.dump(c, cfile, sort_keys=True, indent=4, separators=(',', ': '))
cfile.close()
