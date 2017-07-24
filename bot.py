import importlib
import datetime
import json
import os
import random
import requests
from nose.tools import set_trace
from model import (
    get_one_or_create,
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
        :param modle: A `Bot` object.
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
        self.frequency = self._extract_from_config(config, 'frequency')
        self.state_update_frequency = config.get( 'state_update_frequency', None)
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

    def next_post(self):
        """Find the next unpublished Post, or create a new one.

        :return: A list of Posts.
        """
        # Make sure state is up to date.
        self.check_and_update_state()        
        post = self.model.next_unpublished_post
        if post:
            return post
        
        # Create a new one
        posts = self.new_post()
        if not posts:
            # We didn't do any work.
            posts = []
        if isinstance(posts, Post):
            # We made a single post.
            posts = [posts]
        elif isinstance(posts, basestring):
            # We made a single string, which will become a Post.
            posts = [self.model.create_post(posts)]
        return posts

    def check_and_update_state(self, force=False):
        """Update the bot's internal state, assuming it needs to be updated."""
        if force or self.state_needs_update:
            result = self.update_state()
            if result and isinstance(result, basestring):
                self.model.state = result
            self.model.last_state_update_time = _now()
            _db = Session.object_session(self.model)
            _db.commit()
            return True
        return False

    @property
    def state_needs_update(self):
        """Does this bot's internal state need to be updated?"""
        if self.state_update_frequency is None:
            # This bot doesn't update state on a schedule.
            return False
        now = _now()
        update_at = now + datetime.timedelta(
            minutes=self.state_update_frequency
        )
        last_update = self.model.last_state_update_time
        return not last_update  or last_update > now

    def update_state(self):
        """Update a bot's internal state.

        By default, does nothing.
        """
        pass
        
    def new_post(self):
        """Create a brand new Post.
        
        :return: A string (which will be converted into a Post),
        a Post, or a list of Posts.
        """
        raise NotImplementedError()

    def import_post(self, content):
        """Import a piece of content from some external source into
        a Post.
        
        :content: The input to the post creation process.  By default,
        we treat this as the literal content of a Post object that
        will be posted according to the bot's internal schedule.

        :return: A Post.
        """
        post, is_new = Post.from_content(
            self, content, publish_at=Post.NO_VALUE
        )
        return post
    
    def publish(self, post):
        """Push a Post to every publisher.

        :return: a list of Publications.
        """
        publications = []
        for publisher in self.publishers:
            publication, is_new = get_one_or_create(
                self._db, Publication, service=publisher.service,
                post=post
            )
            if not is_new and not publication.error:
                # There was a previous, successful attempt to publish
                # this Post. Skip this Publisher.

                continue
            try:
                publisher.publish(post, publication)
            except Exception, e:
                message = repr(e.message)
                publication.report_failure("Uncaught exception: %s" % e.message)
            publications.append(publication)
        return publications

    def schedule_next_post(self, last_posts):
        """Determine the best value for BotModel.next_post_time, given that
        `last_posts` were just created.

        BotModel.new_posts() sets BotModel.next_post_time when it
        creates posts, and ensures that new_posts() will not be called
        again until after that time.

        :param last_posts: A list of Posts, the most recent to be
        created.
        """
        # In general, we will not start coming up with new posts again
        # until all the posts that were just created have reached their
        # publication time.
        #
        # However, some bots may have additional configuration that
        # says when a post should happen.
        #
        # We pick the later of the two times.
        latest_published = self.latest_publication_time(last_posts)
        scheduled = self.scheduled_next_publication_time()
        if scheduled and latest_published:
            return max(scheduled, latest_published)
        elif scheduled:
            return scheduled
        else:
            return latest_published

    def latest_publication_time(self, last_posts):
        """The last .publish_at time in the given list of Posts."""
        latest = None
        for p in last_posts:
            if not latest or (p.publish_at and p.publish_at > latest):
                latest = p.publish_at

        return latest

    def scheduled_next_publication_time(self):
        """Assuming that a post happened now, see when the bot configuration
        says the next post should happen.
        """
        how_long = None
        if not self.frequency:
            # The next post should happen immediately.
            return None
        if any(isinstance(self.frequency, x) for x in (int, float)):
            # There should be another post in this number of minutes.
            how_long = self.frequency
        elif 'mean' in self.frequency:
            # There should be another post in a random number of minutes
            # determined by 'mean' and 'stdev'.
            mean = int(self.frequency['mean'])
            stdev = int(self.frequency.get('stdev', mean/5.0))
            how_long = random.gauss(mean, stdev)
        return datetime.datetime.utcnow() + datetime.timedelta(minutes=how_long)

    def stress_test(self, rounds):
        """Perform a stress test of the bot's generative capabilities.

        Your implementation of this method should not have any side effects.
        It should take the current state of the bot and generate `rounds`
        appropriate posts.

        This method is provided for your convenience in testing; you do not
        have to implement it.
        """
        return

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
    
    def new_post(self):
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
                    bot=self.model, content=post, publish_at=now
                )
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
        
    @property
    def url(self):
        raise NotImplementedError()
    

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

