from plugbase import Plugin
from feedparser import feedparser
import threading


class Feed():

    class NotAFeedError():
        pass
    class NoTitleError():
        pass

    titles = []

    def __init__(self, url):
        self.url = url

        feed = feedparser.parse(url)
        if feed.bozo:
            raise Feed.NotAFeedError()
        if not 'title' in feed.feed:
            raise Feed.NoTitleError
        if feed.feed.title in Feed.titles:
            raise IndexError
        self.last_id = feed.entries[0].id
        self.title = feed.feed.title
        Feed.titles.append(feed.feed.title)

    def __str__(self):
        return self.title

    def getLatests(self):
        feed = feedparser.parse(self.url)
        entries = []
        i = 0

        for entrie in feed.entries:
            if entrie.id == self.last_id:
                break
            entries.append(entrie)

        entries.reverse()
        self.last_id = feed.entries[0].id

        return feed.feed, entries


class FeedBot(Plugin):
    """
    RSS feed reader bot
    """
    plugin_name = 'feedbot'

    def __init__(self, bot, settings={}):
        """
        """
        self.feeds = []
        self.feed_worked = None
        self.read_lock = threading.Lock()

        self.cmd = {
            'addfeed':{
                'usage':'addfeed <feed url>',
                'help':'add a feed in fetch list',
                'func':self.add_feed,
            },
            'delfeed':{
                'usage':'delfeed <title>',
                'help':'stop following a feed',
                'func':self.del_feed,
            },
            'readfeeds':{
                'usage':'readfeeds',
                'help':'checks for latest feeds and reset the timer',
                'func':self.read_feeds,
            },
            'savefeeds':{
                'usage':'savefeeds',
                'help':'save current state in feed file',
                'func':self.save_feeds,
            },
            'listfeeds':{
                'usage':'listfeeds',
                'help':'Get a list of all feeds registers',
                'func':self.list_feeds,
            }
        }

        Plugin.__init__(self, bot, settings, True)

    def init(self):
        self.fetch_delay = self.settings.get('fetch delay', 600)
        self.feed_file = self.settings.get('feed file', 'plugins/feedfile')
        self.max_feed = self.settings.get('max feeds', 5)

        self.kill_timer()
        self.create_timer(name='feedtimer', callback=self._read_feeds, delay=self.fetch_delay, start=False, lock=False)

        try:
            f = open(self.feed_file, 'r')
            for url in f.readlines():
                self._add_feed(url)
            f.close()
        except IOError:
            pass

        self.start_timer()

    def on_shutdown(self):
        self._save_feeds()

    def _save_feeds(self):
        try:
            f = open(self.feed_file, 'w')
            for feed in self.feeds:
                f.write(feed.url + '\n')
            f.close()
        except IOError:
            return False
        else:
            return True

    def save_feeds(self, serv, ev, helper):
        if self._save_feeds():
            self.respond(serv, ev, helper, '%s: done' % helper['author'])
        else:
            self.respond(serv, ev, helper, '%s: Something failed' % helper['author'])

    def _add_feed(self, url):
        url = url.strip()
        try:
            f = Feed(url)
            self.feeds.append(f)
        except Feed.NotAFeedError:
            pass
        except Feed.NoTitleError:
            pass
        except IndexError:
            pass

    def add_feed(self, serv, ev, helper, url):
        try:
            f = Feed(url)
            self.feeds.append(f)
        except IndexError:
            self.respond(serv, ev, helper, '%s: this feed is already followed' % helper['author'])
        except Feed.NotAFeedError:
            self.respond(serv, ev, helper, '%s: this do not look as a RSS feed. You may check the link ?' % helper['author']) 
        except Feed.NoTitleError:
            self.respond(serv, ev, helper, '%s: this feed don\'t have a title' % helper['author'])
        else:
            self.respond(serv, ev, helper, '%s: done' % helper['author'])

    def del_feed(self, serv, ev, helper, *title):
        title = ' '.join(title)
        for i in xrange(0, len(self.feeds)):
            if self.feeds[i].title.lower() == title.lower():
                del self.feeds[i]
                self.respond(serv, ev, helper, 'done')
                return True
        self.respond(serv, ev, helper, 'no such feed')
        return False

    def send_feeds(self, channel, entries):
        for entrie in entries:
            msg = '%s: %s (%s) %s' % (
                channel.get('title', 'no title'),
                entrie.get('title', 'no title'),
                entrie.get('author', 'no author'),
                entrie.get('link', 'no link'),
            )
            self.send_to_channels(msg.encode('ascii', 'ignore'))

    def _read_feeds(self):
        self.read_lock.acquire()
        for feed in self.feeds:
            channel, entries = feed.getLatests()
            self.send_feeds(channel, entries)
        self.read_lock.release()

    def read_feeds(self, serv, ev, helper):
        self._read_feeds()
        self.reset_timer()

    def on_timeout(self, timer):
        entries = self._read_feeds()

    def list_feeds(self, serv, ev, helper):
        if not self.feeds:
            self.respond(serv, ev, helper, 'no feeds')
        else:
            self.respond(serv, ev, helper, ', '.join([ f.title for f in self.feeds ]))

