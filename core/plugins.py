"""
utils.plugins - Plugin loading functionality
"""

from pathlib import Path

import importlib
import re

DEPENDS_RE = re.compile(r"\* depends: (.+)")


class PluginLoader(object):
    """
    Infobot's plugin loader.

    Generates a dependency graph and returns a list of loaded modules when
    load_all() is called.
    """
    def __init__(self, plugin_directory="plugins"):
        """ Initializes the PluginLoader by generating a dependency graph """
        self.plugin_package = self.plugin_directory = plugin_directory
        self.graph = {}

        path = Path(self.plugin_directory)
        plugin_paths = []
        for subpath in path.iterdir():
            if (subpath.is_dir() and (subpath / '__init__.py').exists()) or \
               (subpath.name.endswith('.py')):
                plugin_paths.append(subpath)

        for path in plugin_paths:
            self.parseDepends(path)

    def parseDepends(self, path):
        if path.is_dir():
            main_file = str(path / '__init__.py')
        else:
            main_file = str(path)

        with open(main_file) as plugin:
            for line in plugin:
                match = DEPENDS_RE.search(line)
                if match:
                    self.graph[path] = match.group(1).split(', ')
            if path not in self.graph and path.name != '__init__.py':
                # This plugin does not yet define a dependency line.
                # Therefore, we act like it has no dependencies.
                self.graph[path] = []

    def load_plugin(self, plugin_path, name=None):
        if not name:
            name = f"{self.plugin_package}." + plugin_path.stem

        plugin = importlib.import_module(name)
        return plugin

    def load_all(self):
        plugins = []
        self.load_plugin('__init__.py', name='plugins')
        while (self.graph):
            satisfied_plugins = {plugin:deps for plugin,deps in self.graph.items()
                                 if not deps}

            for satisfied_plugin, _ in satisfied_plugins.items():
                plugins.append(self.load_plugin(satisfied_plugin))
                del self.graph[satisfied_plugin]
                for plugin, deps in self.graph.items():
                    # This try clause is here because .remove throws when the
                    # item is not in the list
                    try:
                        deps.remove(satisfied_plugin.stem)
                    except ValueError:
                        pass

        return plugins
