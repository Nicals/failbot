from plugbase import Plugin
from plugbase import PluginNotImplementedError 
from traceback import format_exc
from utils import Log
import traceback


class admin(Plugin):
    """
    Bot administrator.
    """
    plugin_name = 'admin'

    def __init__(self, bot, settings={}, unique=True):
        """
        """
        self.cmd = {
            'enable':{
                'usage':"enable <plugin name>",
                'help':"enable a plugin",
                'func':self.enable
            },
            'disable':{
                'usage':"disable <plugin name>",
                'help':"disable a plugn",
                'func':self.disable
            },
            'reset':{
                'usage':"reset <plugin name>",
                'help':"call init again to reload settings",
                'func':self.reset
            },
            'load':{
                'usage':"load <plugin name> [ enable | disable (default) ]",
                'help':"load a plugin",
                'func':self.load
            },
            'unload':{
                'usage':"unload <plugin name>",
                'help':"unload a plugin",
                'func':self.unload
            },
            'reload':{
                'usage':"reload <plugin name> [ enable | disable ]",
                'help':"unload and load again an existing plugin."
                        "If the plugin was previously enabled (or enabled is asked), enable it.",
                'func':self.reload
            },
            'list':{
                'usage':"list [enabled | disabled | all (default) ]",
                'help':"List plugins. Can apply filters.",
                'func':self.list
            },
            'set':{
                'usage':"set <option> <values> ...",
                'help':"set internal bot option",
                'func':self.set
            },
            'get':{
                'usage':"get [ <option> | all (default)",
                'help':"get internal bot option",
                'func':self.get
            },
            'quit':{
                'usage':"quit",
                'help':"ask captain obvious for this one",
                'func':self.quit
            },
        }

        Plugin.__init__(self, bot, settings, unique=True)

    def init(self):
        self.allowed_users = self.settings['users']

    def on_cmd(self, serv, ev, helper):
        """
        """
        if helper['author'] in self.allowed_users and helper['cmd'] in self.cmd:
            try:
                ret = self.cmd[helper['cmd']]['func'](serv, ev, helper, *helper['args'])
                if ret == True:
                    self.respond(serv, ev, helper,  helper['author'] + ': done')
                elif ret == False:
                    self.respond(serv, ev, helper,  helper['author'] + ': something failed')
            except TypeError:
                self.respond(serv, ev, helper,  helper['author'] + ': something failed, wrong args')
            except SystemExit:
                raise
            except Exception, e:
                self.respond(serv, ev, helper,  helper['author'] + ': something failed, unknown')
                Log.log(Log.log_lvl.ERROR, 'Admin command %s failed. Catches exception %s' % (helper['cmd'], e))
                Log.log(Log.log_lvl.DEBUG, format_exc())

    def enable(self, serv, ev, helper, plug_name):
        return self.bot.enable_plugin(plug_name)

    def disable(self, serv, ev, helper, plug_name):
        return self.bot.disable_plugin(plug_name)

    def reset(self, serv, ev, helper, plug_name):
        return self.bot.reset(plug_name)

    def load(self, serv, ev, helper, plug_name, do_after = 'enable'):
        if do_after not in ('enable', 'disable'):
            return False

        if not self.bot.load_plugin(plug_name):
            return False

        if do_after == 'enable':
            if not self.bot.enable_plugin(plug_name):
                return False

        return True

    def unload(self, serv, ev, helper, plug_name):
        return self.bot.unload_plugin(plug_name)

    def reload(self, serv, ev, helper, plug_name, enable='disable'):
        success = self.bot.reload_plugin(plug_name)
        if not success:
            return False
        if enable == 'enable' or plug_name == self.plugin_name:
            success = self.bot.enable_plugin(plug_name)
        return success

    def list(self, serv, ev, helper, what='all'):
        if what in ('all', 'enabled', 'disabled'):
            for p in self.bot.list_plugins():
                if what == 'all':
                    self.respond(serv, ev, helper,  p[0] + (' [enabled]' if p[1] else ' [disabled]'))
                elif what == 'enabled' and p[1]:
                    self.respond(serv, ev, helper, p[0])
                elif what == 'disabled' and not p[1]:
                    self.respond(serv, ev, helper, p[0])
            return None
        else:
            return False
                    
    def set(self, serv, ev, helper, option, value=None):
        return self.bot.set(option.replace('_', ' '), value)
    
    def get(self, serv, ev, helper, option):
        val = self.bot.get(option.replace('_', ' '))
        if not val:
            self.respond(serv, ev, helper, 'None')
        else:
            self.respond(serv, ev, helper, val)
        return None

    def quit(self, serv, ev, helper):
        self.bot.close()
        return None


