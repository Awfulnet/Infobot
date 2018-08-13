"""
* noload
"""
import importlib
from operator import add
from pathlib import Path
import sys
from collections import defaultdict
from functools import reduce

def _merge_listdict_single(acc, x):
    """ Merges two dictionaries which contain lists.
        Initial value (acc) needs to be a defaultdict. """
    for k, v in x.items():
        acc[k] += v
    return acc

def import_merge(name):
    """ Imports all single-level submodules from a given module name.
        Additionally, merges __callbacks__ and __inits__. """
    module = sys.modules[name]
    modpath = Path(module.__path__[0])
    package = module.__package__

    to_load = []
    for subpath in modpath.iterdir():
        if subpath.name.endswith('.py') and subpath.name != '__init__.py':
            to_load.append('.'+subpath.stem)

    mods = [importlib.import_module(name, package=package) for name in to_load]

    merged_callbacks = reduce(_merge_listdict_single,
                              (getattr(m, '__callbacks__', {}) for m in mods),
                              defaultdict(list))

    merged_inits     = reduce(add, (getattr(m, '__inits__', []) for m in mods))

    setattr(module, '__callbacks__', merged_callbacks)
    setattr(module, '__inits__', merged_inits)

    for mod in mods:
        setattr(module, mod.__name__, mod)
