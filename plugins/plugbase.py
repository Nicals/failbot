import string
from copy import deepcopy
import threading
from traceback import format_exc
from time import sleep


class Timer(threading.Thread):
    """
    This class represents a timer used in plugins
    """
    lock = {}

    def __init__(self, name, callback, delay, start=True, loops=None, lock=True, *args, **kwargs):
        """
        callback: callback function
        delay: in seconds
        start: if the thread is to be started just after its creation
        loops: how many time do we want to call the on_timeout function.
               None to infinity
        lock: each timer have an internal lock arround the callback function.
              set this option to False to disable this lock
        """
        super(Timer, self).__init__(*args, **kwargs)

        self.callback = callback
        self.delay = float(delay)
        self.name = name
        self.loops = loops
        self.stopevent = threading.Event()
        Timer.lock[self.callback] = threading.Lock()
        self.action = None
        self.lock_enabled = lock

        if start:
            self.start()

    def run(self):
        while self.loops is None or self.loops > 0:
            if not self.stopevent.wait(self.delay):
                if self.lock_enabled:
                    Timer.lock[self.callback].acquire()
                self.callback()
                if self.lock_enabled:
                    Timer.lock[self.callback].release()
                if self.loops:
                    self.loops -= 1
            elif self.action == 'stop':
                self.action = None
                self.stopevent.clear()
                break
            elif self.action == 'reset':
                self.action = None
                self.stopevent.clear()

    def stop(self):
        self.stopevent.set()
        self.action = 'stop'

    def reset(self):
        self.stopevent.set()
        self.action = 'reset'


class Plugin():
    """
    Base class for all plugins
    """

    plugin_name = 'generic'
    settings = {}
    unique = True
    cmd = {}
    msg_lock = threading.Lock()

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
        self.timers = {}

        self.cmd['help'] = {
            'usage':'help [ <plugin> | all (default) ]',
            'help':'get some help for a given plugin or all of them',
            'func':self.help
        }

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

    def create_timer(self, name, *args, **kwargs):
        if name in self.timers:
            raise IndexError('A timer with this name already exists')
        self.timers[name] = Timer(name, *args, **kwargs)

    def start_timer(self, name=None):
        if name is None:
            for t in self.timers.values():
                t.start()
        else:
            self.timers[name].start()

    def stop_timer(self, name=None):
        if name is None:
            for t in self.timers.values():
                t.stop()
                t.join()
        else:
            self.timers[name].stop()

    def reset_timer(self, name=None):
        if name is None:
            for t in self.timers.values():
                if t.is_alive():
                    t.reset()
                else:
                    t.start()
        else:
            if self.timers[name].is_alive():
                self.timers[name].reset()
            else:
                self.timers[name].stop()

    def kill_timer(self, name=None):
        self.stop_timer(name)
        if name is None:
            self.timers = {}
        else:
            del self.timers[name]

    def on_join(self, serv, ev):
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

    def on_timeout(self, timer):
        """
        When a timeout event is recieved
        """
        pass

    def _on_shutdown(self):
        """
        Define what a plugin may do when the bot shuts down
        """
        self.kill_timer()
        self.on_shutdown

    def on_shutdown(self):
        pass

    def help(self, serv, ev, helper, plug_name='all', cmd=None):
        """
        Print help for a given plugin.
        """
        help_str = ''
        if plug_name == 'all' or plug_name == self.plugin_name:
            if plug_name == 'all':
                self.respond(serv, ev, helper, '=== %s ===' % self.plugin_name)
                sleep(.7)
            if plug_name != 'all' and cmd is not None:
                if cmd in self.cmd:
                    self.respond(serv, ev, helper, '%s : %s' % (self.cmd[cmd]['usage'], self.cmd[cmd]['help']))
                else:
                    self.respond(serv, ev, helper, 'Unknown cmd.')
            else:
                self.respond(serv, ev, helper, ' | '.join([c for c in self.cmd if c != 'help']))
                sleep(.7)

    def respond(self, serv, ev, helper, msg):
        """
        """
        Plugin.msg_lock.acquire()
        target = helper['chan'] if ev.eventtype() == 'pubmsg' else helper['author']
        serv.privmsg(target, msg)
        Plugin.msg_lock.release()

    def send_to_channels(self, msg):
        Plugin.msg_lock.acquire()
        for channel in self.bot.channels:
            self.bot.connection.privmsg(channel, msg)
        Plugin.msg_lock.release()


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


