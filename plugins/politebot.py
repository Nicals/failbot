from plugbase import Plugin
from random import randint


class politebot(Plugin):

    plugin_name = 'politebot'
    compliments = []
    foo = {}
    base_chance = 30

    def __init__(self, bot, settings={}, unique=True):
        self.cmd = {
            'polite_reload':{
                'usage':'polite_reload',
                'help':'reload compliment file',
                'func':self.load_compliment,
            },
            'polite_stat':{
                'usage':'polite_stat',
                'help':'get an idea of polite state',
                'func':self.get_stats,
            },
            'polite_add':{
                'usage':'polite_add <sentence>',
                'help':'add some polite sentences',
                'func':self.add_sentence,
            },

        }

        Plugin.__init__(self, bot, settings, True)

    def init(self):
        self.base_chance = self.settings['base chance'] if 'base chance' in self.settings else 30
        self.load_compliment(None, None, None)
        for user in self.foo:
            self.foo[user] = self.base_chance

    def load_compliment(self, serv, ev, helper):
        try:
            with open('plugins/politebot', 'r') as f:
                self.compliments = [ l.strip() for l in f.readlines() ]
        except:
            return False
        else:
            return True

    def get_stats(self, serv, ev, helper):
        # serv.privmsg(helper['chan'], str(self.foo))
        self.respond(serv, ev, helper, str(self.foo))
        return None

    def add_sentence(self, serv, ev, helper, *words):
        sentence = ' '.join([ w for w in words])
        if sentence.count('%s') > 1:
            self.respond(serv, ev, helper,  helper['author'] + ': too much format strings...')
            return False

        self.compliments.append(sentence)
        with open('plugins/politebot', 'a') as f:
            f.write(sentence)

        self.respond(serv, ev, helper,  helper['author'] + ': done')
        return True
        
    def on_pubmsg(self, serv, ev, helper):
        author = helper['author']

        if self.compliments:
            if not author in self.foo:
                self.foo[author] = self.base_chance

            if randint(0, self.foo[author]) == 0:
                sentence = self.compliments[randint(0, len(self.compliments) - 1)]
                self.foo[author] = self.base_chance
                if sentence.find('%s') == -1:
                    serv.privmsg(helper['chan'], '%s: %s' % (author, sentence))
                else:
                    serv.privmsg(helper['chan'], sentence % author)
            else:
                self.foo[author] = self.foo[author] - 1


