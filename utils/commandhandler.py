"""
The Command handler
"""
from . import command
from . import get_name
from imp import reload
from importlib import import_module as imp
import sys

BOT = None

class CommandHandler():
    """ The command handler object - handles triggering commands """
    def __init__(self, bot, plugins):
        global BOT
        BOT = bot
        self.initializers = self.commands = []

        self.loaded_plugins = [p.__name__ for p in plugins]

        self.initializers = command.plugins_to_initializers(plugins)
        for function in self.initializers:
            function(bot)
        self.commands = command.plugins_to_commands(plugins)
        self.command_names = [cmd.main_hook for cmd in self.commands]

        self.command_help = self.organize_commands(self.commands)
        self.commands_with_re = [i for i in self.commands if i.regex]
        

        if self.commands == []:
            raise RuntimeError("No commands found!")
        print("%d commands initialized." % (len(self.commands)))

    def reload_plugin(self, plugin):
        if plugin not in sys.modules.keys():
            reloaded_plugin = imp(plugin)
        else:
            reloaded_plugin = reload(sys.modules[plugin])
        if plugin in self.loaded_plugins:
            self.loaded_plugins.remove(plugin)
        for cmd in self.commands:
            if get_name(cmd.function).startswith(plugin):
                self.commands.remove(cmd)
        self.commands += command.plugins_to_commands(reloaded_plugin)
        initializers = command.plugins_to_initializers(reloaded_plugin)
        for i in initializers:
            i(BOT)
        self.command_help = self.organize_commands(self.commands)
        return reloaded_plugin

    def load_plugin(self, name):
        if name in sys.modules.keys():
            return None

        plugin = imp(name)
        self.loaded_plugins.append(plugin.__name__)
        self.commands += command.plugins_to_commands(plugin)
        initializers = command.plugins_to_initializers(plugin)
        for i in initializers:
            i(BOT)
        self.command_help = self.organize_commands(self.commands)
        return plugin

    def unload_plugin(self, name):
        if name not in sys.modules.keys():
            return None
        for cmd in self.commands:
            if get_name(cmd.function).startswith(name):
                self.commands.remove(cmd)
        del sys.modules[name]
        self.loaded_plugins.remove(name)
        return True



    def organize_commands(self, commands):
        categories = set()
        command_help = {}
        categories.add("unknown")
        for command in commands:
            if hasattr(command.function, "_category"):
                categories.add(command.function._category)
        for category in categories:
            command_help.update({category: set()})
        for command in commands:
            if hasattr(command.function, "_category"):
                command_help[command.function._category].add(command.main_hook)
            else:
                command_help["unknown"].add(command.main_hook)
        del categories
        return command_help


    def trigger(self, trigger):
        """ Try to trigger a command with hook <trigger> """
        for command_ in self.commands:
            if command_.is_triggered_by(trigger):
                return command_

        return None

    def trigger_short(self, trigger):
        """ Try to trigger a command with shorthook <trigger> """
        for command_ in self.commands:
            if command_.is_triggered_by(trigger, short=True):
                return command_

        return None
