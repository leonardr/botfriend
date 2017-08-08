# encoding: utf-8
import importlib
import datetime
import json
import os
import random
import requests
from nose.tools import set_trace
from model import (
    get_one_or_create,
    InvalidPost,
    Post,
    Publication,
    _now,
)
from sqlalchemy.orm.session import Session


class Bot(object):
    """Bot implements the creative part of a bot.

    This is as distinct from BotModel in model.py, which implements
    the part that deals with scheduling posts, managing the archive,
    and delivering the creative output to various services.
    """

    # A good generic time format.
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # The time format used by HTTP (UTC only)
    HTTP_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
    
    @property
    def log(self):
        return self.model.log
    
    def __init__(self, model, directory, config):
        """
        :param model: A `Bot` object.
        :param directory: The directory from which the bot code was
            loaded.
        :param config: A dictionary containing bot-specific configuration
            from bot.yaml in `directory.`
        """
        self._db = Session.object_session(model)
        self.model = model
        self.name = self.model.name
        self.base_directory, self.module_name = os.path.split(directory)
        self.directory = directory
        self.config = config
        self.schedule = self._extract_from_config(config, 'schedule')
        self.state_update_schedule = config.get( 'state_update_schedule', None)
        publishers = self.config.get('publish', {})
        if not publishers:
            self.log.warn("Bot %s defines no publishers.", self.name)
        self.publishers = [
            Publisher.from_config(self, module, config)
            for module in publishers
        ]
        
    def _extract_from_config(self, config, key):
        value = config.get(key, None)
        if (value
            and isinstance(value, list)
            and len(value) == 1 and isinstance(value[0], dict)
        ):
            return value[0]
        return value

    # Methods dealing with creating new posts

    @property
    def publishable_posts(self):
        """Find the Posts that can be published right now, creating a new one
        if necessary.

        :return: A list of Posts that should be published right now.
        """
        # Make sure state is up to date.
        self.check_and_update_state()        

        posts = self.model.ready_scheduled_posts
        if posts:
            # One or more scheduled posts need to be published immediately.
            return posts

        if not self.model.should_make_new_post:
            # It's not time to make a new post.
            return []

        # Beyond this point, we either have something to post or we
        # want to make a new post.
        
        # Look in the backlog for an object we can convert into a post.
        posts = self.model.pop_backlog()
        if not posts:
            # Create a new post
            posts = self.new_post()
        
        if not posts:
            # We didn't actually do any work. (This probably shouldn't
            # happen.) Return immediately so as not to update the post
            # schedule.
            return []

        # Schedule the next post time. This will hopefully be
        # overwritten after the new posts are published, but doing it
        # now prevents a large number of unpublishable posts from being
        # created when a publisher isn't working.
        self.schedule_next_post()
        return self._to_post_list(posts)

    def _to_post_list(self, obj):
        """Take the output of a post generation process and make
        sure it becomes a list of Posts.
        """
        def is_list_of_posts(posts):
            return (
                isinstance(posts, list) and
                all(isinstance(i, Post) for i in posts)
            )
        
        if isinstance(obj, Post):
            # It's already a Post.
            return [obj]
        if is_list_of_posts(obj):
            # It's already a list of Posts.
            return obj
        posts = self.object_to_post(obj)
        if isinstance(posts, basestring):
            post, is_new = Post.from_content(self.model, posts)
            return [post]
        if isinstance(posts, Post):
            return [posts]
        if is_list_of_posts(posts):
            # It's already a list of Posts.
            return posts
        raise InvalidPost(
            "object_to_post must return a Post or a list containing only Posts. (got %r)" % posts
        )
        
    
    def new_post(self):
        """Create a new post for immediate publication.

        :return: A Post, a list of Posts (all of which will be
        published immediately), or some other object such as a string
        (which will be passed into object_for_post for conversion into
        a post).
        """
        raise NotImplementedError()

    def object_to_post(self, obj):
        """Turn an object retrieved from backlog or from new_post(), into a
        Post object.

        The default implementation assumes `obj` is a string to be used
        as the content of the post.
        """
        return obj
    
    def stress_test(self, rounds):
        """Perform a stress test of the bot's generative capabilities.

        Your implementation of this method should not have any side effects.
        It should take the current state of the bot and generate `rounds`
        appropriate posts.

        This method is provided for your convenience in testing; you do not
        have to implement it.
        """
        return
    
    # Methods dealing with bot state.
    
    def check_and_update_state(self, force=False):
        """Update the bot's internal state, assuming it needs to be updated."""
        if force or self.state_needs_update:
            result = self.update_state()
            if result:
                self.model.state = result
            _db = Session.object_session(self.model)
            _db.commit()
            return True
        return False

    @property
    def state_needs_update(self):
        """Does this bot's internal state need to be updated?"""
        if self.state_update_schedule is None:
            # This bot doesn't update state on a schedule.
            return False
        now = _now()
        update_at = now + datetime.timedelta(
            minutes=self.state_update_schedule
        )
        last_update = self.model.last_state_update_time
        return not last_update or now > update_at

    def update_state(self):
        """Update a bot's internal state.

        By default, does nothing.
        """
        pass

    # Methods dealing with backlog posts
        
    @property
    def backlog(self):
        """Return a bot's backlog as a list of strings."""
        return self.model.backlog

    def extend_backlog(self, items):
        backlog = self.model.backlog
        for item in items:
            backlog.append(self.backlog_item(item))
        self.model.backlog = backlog

    def backlog_item(self, data):
        """Convert an input string into a backlog item.

        The default behavior is to treat the line as the content for
        the backlog item.
        """
        return data
        
    def clear_backlog(self):
        """Clear a bot's backlog."""
        self.model.backlog = []
        
    # Methods dealing with scheduling posts.
    
    def schedule_posts(self):
        """Create some number of posts to be published at specific times.

        It's better to override _schedule_posts() -- this method
        just calls that method and does some error checking.
        
        :return: A list of newly scheduled Posts.
        """
        scheduled = self._schedule_posts()
        if isinstance(scheduled, Post):
            scheduled = [scheduled]
        now = _now()
        for post in scheduled:
            if post.publish_at and post.publish_at < now:
                raise InvalidPost(
                    "A new post can't be scheduled for the past. (%s was scheduled for %s)" % (
                        post.content.encode("ascii", errors="replace"), post.publish_at
                    )
                )
        return scheduled

    def _schedule_posts(self):
        """
        By default, this does nothing. This is an advanced feature for
        bots like Mahna Mahna that need to post at specific
        times. Most bots should be able to use the default scheduler,
        and either generate posts on demand or put posts into
        Bot.backlog.
        """
        return []
        
    def schedule_next_post(self):
        """Assuming that a post was just published, set the time at which the
        next post should be published.
        """
        how_long = self._next_scheduled_post
        if how_long:
            self.model.next_post_time = _now() + how_long

    @property
    def _next_scheduled_post(self):
        how_long = None
        if not self.schedule:
            # This bot schedules individual posts in advance rather than
            # relying on a timer-based schedule. Posts should happen as
            # they're scheduled.
            return None
        if any(isinstance(self.schedule, x) for x in (int, float)):
            # There should be another post in this number of minutes.
            how_long = self.schedule
        elif 'mean' in self.schedule:
            # There should be another post in a random number of minutes
            # determined by 'mean' and 'stdev'.
            mean = int(self.schedule['mean'])
            stdev = int(self.schedule.get('stdev', mean/5.0))
            how_long = random.gauss(mean, stdev)
        return datetime.timedelta(minutes=how_long)

    # Methods dealing with publishing posts.
    
    def publish(self, post):
        """Push a Post to every publisher.

        :return: a list of Publications.
        """
        if post.publish_at and post.publish_at > _now():
            # This should never happen; the method should not have been
            # called.
            logging.warn(
                "Not publishing %s until %s", post.content,
                post.publish_at.strftime(self.TIME_FORMAT)
            )
            return
        
        publications = []
        for publisher in self.publishers:
            publication, is_new = self.make_publication(
                publisher, post
            )
            if not is_new and not publication.error:
                # There was a previous, successful attempt to publish
                # this Post. Skip this Publisher.
                continue
            try:
                self.post_to_publisher(publisher, post, publication)
            except Exception, e:
                message = repr(e.message)
                publication.report_failure("Uncaught exception: %s" % e.message)
            publications.append(publication)

        # Update the time at which we will try to publish the next post.
        self.schedule_next_post()
        return publications

    def make_publication(self, publisher, post):
        """Create a Publication for this Publisher and this Post.
        
        This is your chance to modify the content of the Post for
        different publishers.
        """
        return get_one_or_create(
            self._db, Publication, service=publisher.service,
            post=post
        )
    
    def post_to_publisher(self, publisher, post, publication):
        return publisher.publish(post, publication)
    

class TextGeneratorBot(Bot):
    """A bot that comes up with a new piece of text every time it's invoked.
    """
    def new_post(self):
        """Create a brand new Post.

        :return: Some text.
        """
        # Make sure state is up to date.
        self.check_and_update_state()
        return self.generate_text()
        
    def generate_text(self):
        raise NotImplementedError()

    def stress_test(self, rounds):
        for i in range(rounds):
            print self.generate_text()
    

class Publisher(object):

    """A way of publishing the output of a bot."""

    @classmethod
    def from_config(cls, bot, module, full_config):
        publish_config = full_config.get('publish', {})
        module_config = publish_config.get(module)
        
        # Try both publish.foo and publish._foo, in case the module
        # needs to import a package called 'foo' from elsewhere (see
        # _mastodon.py for an example.)
        publisher_module = None
        names = ('publish.' + module, 'publish._' + module)
        for module_name in names:
            try:
                publisher_module = importlib.import_module(module_name)
                break
            except ImportError, e:
                pass
        if not publisher_module:
            raise ImportError(
                "Could not import publisher for %s; tried %s" % (
                    module, ", ".join(names)
                )
            )
        publisher_class = getattr(publisher_module, "Publisher", None)
        if not publisher_class:
            raise Exception(
                "Loaded module %s but could not find a class called Publisher inside." % bot_module
            )
        try:
            publisher = publisher_class(bot, full_config, module_config)
        except Exception, e:
            raise Exception(
                "Could not import %s publisher for %s: %s" % (
                    module_name, bot.name, e.message
                )
            )
        publisher.service = module
        return publisher
    
    def __init__(self, service_name, bot, full_config, **config):
        self.service_name=service_name
        self.bot = bot

    def publish(self, post, publication):
        """Publish the content of the given Post object.

        This probably includes text but may also include binary
        objects.

        :param post: A Post object.
        :param previous_attempt: A Publication object describing the
           attempt to publish this post. It may have data left in it
           from a previous publication attempt.
        """
        raise NotImplementedError()


class ScraperBot(Bot):
    """This bot downloads a resource via HTTP and extracts dated posts from 
    it.

    The bot's state contains the last update time, for use in making
    HTTP conditional requests.
    """

    def __init__(self, model, directory, config):
        super(ScraperBot, self).__init__(model, directory, config)
        if 'url' in config:
            self._url = config['url']
        
    @property
    def url(self):
        return self._url
    
    def new_post(self):
        """Scrape the site and get a number of new Posts out of it."""
        headers = self.headers
        response = requests.get(self.url, headers=headers)
        if response.status_code == 304: # Not Modified
            return
        utcnow = datetime.datetime.utcnow()
        now = _now()
        new_last_update_time = None
        posts = []
        for post in self.scrape(response):
            if not isinstance(post, Post):
                post, ignore = Post.from_content(
                    bot=self.model, content=post
                )
            if not post.publish_at:
                post.publish_at = now
            posts.append(post)
        self.model.last_state_update_time = utcnow
        return posts
        
    @property
    def headers(self):
        headers = {}
        if self.model.last_state_update_time:
            headers['If-Modified-Since'] = self.model.last_state_update_time.strftime(
                self.HTTP_TIME_FORMAT
            )
        return headers


class RSSScraperBot(ScraperBot):
    """Scrapes an RSS or Atom feed and creates a Post for each item."""

    TWEET_TEMPLATE = u"‘%(title)s’: %(link)s"
    
    def scrape(self, response):
        import feedparser
        feed = feedparser.parse(response.content)
        feed_data = self.prepare_feed(feed)
        entries = []
        for entry in feed['entries']:
            obj = self.parse_entry(feed_data, entry)
            if obj:
                entries.append(obj)
        return entries

    def prepare_feed(self, feed):
        """Derive any common information from the feed.

        This object will be passed into every parse_entry call.

        By default, returns the feed itself.
        """
        return feed

    def parse_entry(self, feed_data, entry):
        """Turn an entry into a Post."""
        id = entry['id']
        post, is_new = Post.for_external_key(self, id)
        if is_new:
            post.content = self.TWEET_TEMPLATE % entry
            return post
        
    
class RetweetBot(Bot):
    """Instead of posting new text, this Twitter-specific bot looks at
    the tweets posted from some other account since the last time it
    ran, and retweets the most popular one.
    """
    # We arbitrarily count retweets for twice as much as favorites.
    RETWEET_COEFFICIENT = 2
    
    def __init__(self, model, directory, config):
        super(RetweetBot, self).__init__(model, directory, config)
        self.retweet_user = config['retweet-user']
        for publisher in list(self.publishers):
            if publisher.service == 'twitter':
                self.twitter = publisher.api
                # We don't actually want to publish anything to Twitter,
                # we just need the Twitter client for something else.
                self.publishers.remove(publisher)
                break
        else:
            raise ValueError("No Twitter publisher configured, cannot continue.")

    def score(self, tweet):
        """Calculate a semi-arbitrary score for this tweet."""
        if not tweet:
            return 0
        return (
            tweet.retweet_count*self.RETWEET_COEFFICIENT
        ) + tweet.favorite_count
        
    def new_post(self):
        """Retweet someone else's post and store it locally.
        """
        kwargs = dict(screen_name=self.retweet_user, count=200)
        max_id = self.model.json_state
        if max_id:
            kwargs['since_id'] = max_id
        timeline = self.twitter.user_timeline(**kwargs)
        max_id = None
        most_popular = None
        if not timeline:
            # No tweets since last time. Do nothing.
            return
        for tweet in timeline:
            if not max_id or tweet.id > max_id:
                max_id = tweet.id
            if not most_popular or self.score(tweet) > most_popular:
                most_popular = tweet
        if self.score(most_popular) == 0:
            # Just pick one rather than always choosing the most recent.
            most_popular = random.choice(timeline)
        self.twitter.retweet(most_popular.id)
        self.model.state = json.dumps(max_id)

        # Return the text of the tweet we retweeted, so that it can be stored
        # in the database and published through other publishers, such as a
        # local log.
        return most_popular.text

