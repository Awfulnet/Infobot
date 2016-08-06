"""
utils.plugins - Plugin loading functionality
"""

import re
import fnmatch
import os

from importlib.machinery import SourceFileLoader

DEPENDS_RE = re.compile(r"\* depends: (.+)")

class PluginLoader(object):
    """
    The plugin loader
    Generates a dependency graph and returns a list of loaded modules
    when load_all() is called.
    """
    def __init__(self):
        """ Initializes the PluginLoader by generating a dependency graph """
        self.directory = './plugins'
        self.graph = {}
        files = fnmatch.filter(os.listdir('./plugins'), "*.py")
        for f in files:
            self.parseDepends(f)

    def parseDepends(self, f):
        with open(os.path.join(self.directory, f)) as fobj:
            for line in fobj:
                match = DEPENDS_RE.search(line)
                if match:
                    self.graph[f] = match.group(1).split(', ')
            if f not in self.graph and f != '__init__.py':
                # This plugin does not yet define a dependency line, and therefore has no dependencies
                self.graph[f] = []

    def load_plugin(self, plugin_filename, name=None):
        if name is None:
            name = "plugins." + plugin_filename[:-3]
        plugin = SourceFileLoader(name, os.path.join(self.directory, plugin_filename)).load_module()
        return plugin

    def load_all(self):
        plugins = []
        self.load_plugin('__init__.py', name='plugins')
        while (self.graph):
            satisfied_plugins = dict(filter(lambda x: not x[1], self.graph.items()))
            for satisfied_plugin, _ in satisfied_plugins.items():
                plugins.append(self.load_plugin(satisfied_plugin))
                del self.graph[satisfied_plugin]
                for plugin, deps in self.graph.items():
                    # This try clause is here because .remove errors when the item is not in the list
                    try:
                        deps.remove(satisfied_plugin[:-3])
                    except ValueError:
                        pass
        return plugins
