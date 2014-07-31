""" 
Initialization file for plugin directory.
"""
import os, sys, types
__all__ = []

_dir = "./plugins"

for file_ in os.listdir(_dir):
    if file_.endswith(".py"):
        __all__.append(file_.split(".")[0])

[__import__(__name__, fromlist=[item]) for item in __all__]
CURRENT_MODULE = sys.modules[__name__]

_MODULETYPE = types.ModuleType

def get_plugins():
    """ Get the plugins. """
    _plugins = []
    for key, attribute in CURRENT_MODULE.__dict__.items():
        if not key.startswith("_") and attribute != CURRENT_MODULE:
            if attribute != get_plugins and type(attribute) == _MODULETYPE:
                _plugins.append(attribute)
    return _plugins

del os
del sys
del types