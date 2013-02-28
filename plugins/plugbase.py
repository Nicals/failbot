import string
from copy import deepcopy
from traceback import format_exc
from time import sleep

class Plugin():
    """
    Base class for all plugins
    """

    plugin_name = 'generic'
    settings = {}
    unique = True
    cmd = {}

    def __init__(self, bot, settings={}, unique = True):
        """
        """
        # check if the plugin seems well formated
        if self.plugin_name == 'generic':
            raise(PluginNoNameError())
        if 1 in [c in self.plugin_name for c in string.whitespace]:
            raise(PluginNameFormatError(self.plugin_name))
        if unique == False:
            raise(PluginNotImplementedError('unique'))

        self.settings = deepcopy(settings)
        self.bot = bot
        self.unique = unique

        # self.cmd['help'] = {
        #     'usage':'help [ <plugin> | all (default) ]',
        #     'help':'get some help for a given plugin or all of them',
        #     'func':self.help
        # }

        self.init()

    def __str__(self):
        return self.plugin_name

    
    def __repr__(self):
        return str({'name':self.plugin_name, 'settings':self.settings})


    def base_init(self, settings={}):
        """
        """
        self.settings = deepcopy(settings)
        self.init()


    def init(self):
        """
        """
        pass


    def on_pubmsg(self, serv, ev, helper):
        """
        Helper is a dict containing:
            event: event type
            author: nickname of author
            author_nm: nickname + nickmask
            chan:
            msg
        """
        pass

    def on_privmsg(self, serv, ev, helper):
        """
        Helper is a dict containing:
            event: event type
            author: nickname of author
            author_nm: nickname + nickmask
            chan:
            msg
        """
        pass

    def on_cmd(self, serv, ev, helper):
        """
        Helper is a dict containing
            event: event type
            author: nickname of author
            author_nm: nickname + nickmask
            cmd: name of the command
            args: argument after the command (list)
        """
        if helper['cmd'] in self.cmd:
            self.cmd[helper['cmd']]['func'](serv, ev, helper, *helper['args'])


    def help(self, serv, ev, helper, plug_name='all'):
        """
        Print help for a given plugin.
        """
        return True 

        help_str = ''
        if plug_name == 'all' or plug_name == self.plugin_name:
            if plug_name == 'all':
                help_str = '=== ' + self.plugin_name + ' ===\n'
            for c in self.cmd.values():
                help_str = help_str = c['usage'] + "\n> " + c['help'] + "\n"
            serv.privmsg(helper['chan'], help_str)
            sleep(1)



class PluginError(Exception):
    """
    Raised if the plugin doesn't have a name defined
    """

    def __init__(self, value = ''):
        self.value = value

    def __str__(self):
        return 'Plugin error: ' + str(self.value)


class PluginNoNameError(PluginError):
    """
    Raised if no name is defined for the plugin
    """

    def __str__(self):
        return 'Plugin error: no name implemented'

class PluginNameFormatError(PluginError):
    """
    Raised if the name contains whitespaces
    """
    def __str__(self):
        return 'Plugin error: wrong format for name \'' + str(self.value) + '\''


class PluginNotImplementedError(PluginError):
    """
    Raised if we intent to do something not implemented
    """

    def __str__(self):
        return 'Plugin Error: ' + str(self.value) + ' not implemented'


