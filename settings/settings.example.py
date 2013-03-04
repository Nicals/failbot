
##
## Failbot settings file
##
##   Rename this file to settings.py
##


# failbot options
settings = {
    # server and port to connect to.
    'server':'irc.freenode.org',
    'port':6667,
    # channels to connect to. tupple (chan, password)
    'channels':[
        ('#channel', 'password'),
        ('#other_channel', None),
    ],
    # nickname of the bot
    'nickname':'failbot',
    'realname':'failbot',
    # password to "/msg nickserv identify " cmd
    'password':None,
    # how long the bot should wait before trying to reconnect
    'reconnect interval':60,
    # which prefix to use to send a command to Mr Bot ?
    'cmd prefix':'!',
    # verbosity and log file. Set log file to None for stdout
    # 0 : nothing
    # 1 : error
    # 2 : warning
    # 3 : info
    # 4 : debug
    'verbose':2,
    'log file':None,
    # pid file. default is /tmp/failbot.pid
    'pid file':'/tmp/failbot.pid',
}


# list here all plugins to enable on startup
enabled_plugins = [
    'testplug',
    'admin',
]


# custom settings for plugins.
plugin_settings = {
    'admin':{
        'users':['Nicals']
    },
}
