#!/usr/bin/python

from os import listdir, path, fork, kill, unlink
from irc import irclib
from irc import ircbot
from plugins.plugbase import Plugin
from sys import modules, exit
from signal import signal, SIGINT, SIGQUIT
from settings import settings
from traceback import format_exc
from copy import deepcopy
from utils import Log
from argparse import ArgumentParser
from importlib import import_module
from plugins.plugbase import Plugin


class FailBot(ircbot.SingleServerIRCBot):
    """
    """
    # dict  <plugin_name>:<class>
    plugins = {}
    # instance of plugins
    enabled_plugins = []
    # a copy of the generic settings in module settings
    settings = {}

    def __init__(self, settings, plugins):
        """
        """

        self.settings = {
            'nickname':settings.get('nickname', 'failbot'),
            'password':settings['password'],
            'realname':settings.get('realname', 'failbot'),
            'reconnect interval':settings.get('reconnect interval', 60),
            'quit message':settings.get('quit message', 'I\'m out.'),
            'verbose':settings.get('verbose', Log.log_lvl.ERROR),
            'log file':settings.get('log file', None),
            'server':settings['server'],
            'port':settings['port'],
            'channels':settings['channels'],
            'cmd prefix':settings.get('cmd prefix', '!'),
        }

        Log.verbosity = self.settings['verbose']
        Log.setLogFile(self.settings['log file'])

        Log.log(Log.log_lvl.DEBUG, 'Settings loaded: %s' % self.settings)

        ircbot.SingleServerIRCBot.__init__(self,
                                    server_list = [(
                                        self.settings['server'],
                                        self.settings['port']
                                    )],
                                    nickname = self.settings['nickname'],
                                    realname = self.settings['realname'],
                                    reconnection_interval = self.settings['reconnect interval']
                               )
        Log.log(Log.log_lvl.INFO, 'Connection to %s:%d' % (settings['server'], settings['port']))

        # load some plugins
        for f in [ path.splitext(f)[0] for f in listdir(path.dirname(path.realpath(__file__)) + '/plugins')
                                           if f.endswith('.py') and f != '__init__.py' and f != 'plugbase.py' ]:
            if self.load_plugin(f):
                if f in plugins:
                    self.enable_plugin(f)

        Log.log(Log.log_lvl.INFO,
                    "\n".join([p[0] + (' [enabled]' if p[1] else ' [disabled]') for p in self.list_plugins()]))

    def close(self):
        """
        Shutdown failbot
        """
        for p in self.enabled_plugins:
            p._on_shutdown()

        self.connection.disconnect(self.settings['quit message'])
        Log.close()
        exit(0)

    def load_plugin(self, plug_name):
        """
        Load a module in plugins package.
        The module must (MUST !) have one subclass of Plugin in it.
        """
        import_string = 'from plugins import %s' % plug_name
        try:
            # don't even try to import if the plugin is already loaded
            if not 'plugins.' + plug_name in modules:
                mod = import_module('plugins.%s' % plug_name)
                candidates = []
                # Find a unique class that is subclass of Plugin in the module
                for attr in dir(mod):
                    try:
                        candidate = getattr(mod, attr)
                        if issubclass(candidate, Plugin) and candidate is not Plugin:
                            candidates.append(candidate)
                    except TypeError:
                        pass

                if len(candidates) != 1:
                    Log.log(Log.log_lvl.ERROR, 'cannot load plugin {p} : one and only one plugin class must be defined in plugins.{p}.'.format(p=plug_name))
                    return False

                self.plugins[plug_name] = candidates[0]

                return True
            else:
                Log.log(Log.log_lvl.WARNING, 'failed to load plugin %s. seems already loaded.' % plug_name)

                return False
        except ImportError:
            Log.log(Log.log_lvl.ERROR, 'Cannot load %s, module do not exists' % plug_name)
            return False
        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Failed to load plugin %s. Catches exception ' % e)
            Log.log(Log.log_lvl.DEBUG, format_exc())

            return False

    def unload_plugin(self, plug_name):
        """
        """
        try:
            if 'plugins.' + plug_name in modules:
                self.disable_plugin(plug_name, disable_all = True)
                del self.plugins[plug_name]
                del modules['plugins.' + plug_name]
                Log.log(Log.log_lvl.INFO, 'plugin %s unloaded ' % plug_name)
                
                return True
            else:
                Log.log(Log.log_lvl.WARNING, 'cannot unload plugin %. plugin not loaded' % plug_name)

                return False
        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Failed to unload plugin %s. Catches exception %s' % (plug_name, e))
            Log.log(Log.log_lvl.DEBUG, format_exc())

            return False

    def reload_plugin(self, plug_name):
        """
        Reload a module. If the plugin is not already loaded, this method acts as load_plugin.
        """
        if plug_name not in self.plugins or 'plugins.' + plug_name not in modules:
            Log.log(Log.log_lvl.WARNING, 'cannot reload %s, plugin not loaded. Failbot will load it.' % plug_name)
            return self.load_plugin(plug_name)

        try:
            plugin_cname = self.plugins[plug_name].__name__
            self.disable_plugin(plug_name)
            reload(modules['plugins.%s' % plug_name])
            self.plugins[plug_name] = getattr(modules['plugins.%s' % plug_name], plugin_cname)
            Log.log(Log.log_lvl.INFO, 'plugin %s reloaded' % plug_name)
        except ImportError:
            Log.log(Log.log_lvl.ERROR, 'cannot reload %s, no module found.' % plug_name)
            return False

        return True

    def enable_plugin(self, plug_name):
        """
        """
        try:
            # check if it needs to be unique
            if self.plugins[plug_name].unique:
                for p in self.enabled_plugins:
                    if isinstance(p, self.plugins[plug_name]):
                        Log.log(Log.log_lvl.ERROR, 'Failed to enable plugin %s which is not instance of Plugin.' % plug_name)

                        return False
            plug_settings = settings.plugin_settings[plug_name] if plug_name in settings.plugin_settings else {}
            self.enabled_plugins.append(self.plugins[plug_name](self, plug_settings))
        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Failed to enable plugin %s. Catches exception ' % e)
            Log.log(Log.log_lvl.DEBUG, format_exc())

            return False
        else:
            Log.log(Log.log_lvl.INFO, 'Enable %s.' % plug_name)

            return True

    def disable_plugin(self, plug_name, disable_all=False):
        """
        """
        try:
            to_del = []
            i = 0

            for p in self.enabled_plugins:
                if p.plugin_name == plug_name:
                    to_del.append(i)
                    if self.plugins[plug_name].unique or not disable_all:
                        break
                i = i + 1

            to_del.reverse()

            for a in to_del:
                del self.enabled_plugins[a]

        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Failed to disable plugin %s. Catches exception %s' % (plug_name, e))
            Log.log(Log.log_lvl.DEBUG, format_exc())

            return False
        else:
            Log.log(Log.log_lvl.INFO, 'Disable %s.' % plug_name)

            return True

    def list_plugins(self):
        """
        """
        plug_list = []
        for p in self.plugins:
            plug_list.append((p, p in [ pl.plugin_name for pl in self.enabled_plugins]))

        return plug_list


    def get(self, opt):
        if opt in self.settings:
            return str(self.settings[opt])

        return False

    def set(self, opt, val):
        if opt == 'cmd prefix':
            self.settings[opt] = val
        elif opt == 'verbose':
            val = int(val)
            if val in range(Log.log_lvl.NONE, Log.log_lvl.DEBUG + 1):
                self.settings[opt] = val
                Log.verbosity = self.settings[opt]
            else:
                return False
        elif opt == 'log file':
            self.settings[opt] = val
            Log.setLogFile(self.settings[opt])
        else:
            return False

        return True

    def reset(self, plug_name = None):
        """
        Reset plugins. Reload plugin module and settings.
        If plug_name is None, all plugins are reloaded
        If plug_name is a list, all plugin within this list will be reloaded.
        If plug_name is a str, just this plugin will be reloaded
        """
        try:
            reload(modules['settings.settings'])
            plug_name = [] if not plug_name else [str(plug_name)] if not isinstance(plug_name, list) else plug_name

            for plug in plug_name:
                plug_in = [ p for p in self.enabled_plugins if p.plugin_name == plug ]
                for p in plug_in:
                    p.base_init(settings.plugin_settings[plug] if plug in settings.plugin_settings else {})
        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Failed to reset plugin %s. Catches exception %s' % (', '.join(plug_name), e))
            Log.log(Log.log_lvl.DEBUG, format_exc())

            return False
        else:
            Log.log(Log.log_lvl.INFO, 'Reset %s' % ', '.join(plug_name))

            return True

    def on_welcome(self, serv, ev):
        """
        On welcome, join channels sets in settings.
        """
        if self.settings['password']:
            serv.privmsg('nickserv', 'identify %s' % self.settings['password'])
        for c in self.settings['channels']:
            channel = c[0] + ' ' + c[1] if c[1] else ''
            Log.log(Log.log_lvl.INFO, 'joining %s' % channel)
            serv.join(channel)

    def on_join(self, serv, ev):
        for p in self.enabled_plugins:
            p.on_join(serv, ev)

    # TODO: may be some plugins want to save some stuff here ?
    def on_disconnect(self, serv, ev):
        """
        """
        pass

    def on_pubmsg(self, serv, ev):
        """
        If the published message is a command, format helper as a command,
        else format as a message.
        Call on_pubmsg for all enabled plugins.
        """
        try:
            helper = {
                'event':ev.eventtype(),
                'author':irclib.nm_to_n(ev.source()),
                'author_nm':ev.source(),
                'chan':ev.target(),
                'msg':ev.arguments()[0].strip(),
            }

            if helper['msg'][0] == self.settings['cmd prefix']:
                helper['event'] = 'cmd'
                helper['cmd'] = helper['msg'].split(' ')[0][1:]
                helper['args'] = helper['msg'].split(' ')[1:]
                del helper['msg']

                for p in self.enabled_plugins:
                    p.on_cmd(serv, ev, helper)
            else:
                for p in self.enabled_plugins:
                    p.on_pubmsg(serv, ev, helper)

        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Fail to process pubmsg event. Catches exception %s' % e)
            Log.log(Log.log_lvl.DEBUG, format_exc())

    def on_privmsg(self, serv, ev):
        """
        If the published message is a command, format helper as a command,
        else format as a message.
        Call on_privmsg for all enabled plugins.
        """
        try:
            helper = {
                'event':ev.eventtype(),
                'author':irclib.nm_to_n(ev.source()),
                'author_nm':ev.source(),
                'chan':ev.target(),
                'msg':ev.arguments()[0].strip(),
            }

            if helper['msg'][0] == self.settings['cmd prefix']:
                helper['event'] = 'cmd'
                helper['cmd'] = helper['msg'].split(' ')[0][1:]
                helper['args'] = helper['msg'].split(' ')[1:]
                del helper['msg']

                for p in self.enabled_plugins:
                    p.on_cmd(serv, ev, helper)
            else:
                for p in self.enabled_plugins:
                    p.on_privmsg(serv, ev, helper)

        except Exception, e:
            Log.log(Log.log_lvl.ERROR, 'Fail to process privmsg event. Catches exception %s' % e)
            Log.log(Log.log_lvl.DEBUG, format_exc())


# need this global instance to be used by the signal handler
failbot = None


def signal_handler(signum, frame):
    """
    Cleanly exits the program
    """
    if signum == SIGINT or signum == SIGQUIT:
        failbot.close()


if __name__ == '__main__':

    parser = ArgumentParser(description='A simple IRC bot with plugin support.')
    parser.add_argument('-d', '--daemonize', default=False, action='store_true', help='start as daemon')
    parser.add_argument('-k', '--kill', default=False, action='store_true', help='kill existing daemon')

    args = parser.parse_args()

    daemonize = args.daemonize
    exit_daemon = args.kill

    signal(SIGINT, signal_handler)
    signal(SIGQUIT, signal_handler)

    pid_file = settings.settings.get('pid file', '/tmp/failbot.pid')

    if daemonize:
        # only one instance of failbot is allowed
        if not path.isfile(pid_file):
            try:
                pid = fork()

                if pid != 0:
                    with open(pid_file, 'w') as f:
                        f.write(str(pid))
                    print 'Failbot started [%d]' % pid
                    exit(0)
            except Exception, e:
                print 'Cannot fork. %s' % str(e)
                exit(71)
        else:
            with open(pid_file, 'r') as f:
                pid = int(f.read())
                print 'Cannot run as daemon, another instance is already running [%d]' % pid
            exit(1)

    if exit_daemon:
        with open(pid_file, 'r') as f:
            pid = int(f.read())
        try:
            kill(pid, SIGINT)
        except Exception, e:
            print 'Cannot kill process [%d]: %s' % (pid, str(e))
            exit(71)
        print 'failbot stopped [%d]' % pid
    else:
        failbot = FailBot(settings.settings, settings.enabled_plugins)
        try:
            failbot.start()
        except SystemExit:
            if daemonize:
                unlink(pid_file)


