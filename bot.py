import importlib
import datetime
import random
from nose.tools import set_trace
from model import (
    get_one_or_create,
    Post,
    Publication,
)
from sqlalchemy.orm.session import Session


class Bot(object):
    """Bot implements the creative part of a bot.

    This is as distinct from BotModel in model.py, which implements
    the part that deals with scheduling posts, managing the archive,
    and delivering the creative output to various services.
    """

    @property
    def log(self):
        return self.model.log
    
    def __init__(self, model, module_name, config):
        self._db = Session.object_session(model)
        self.model = model
        self.module_name = module_name
        self.name = self.model.name
        self.config = config
        self.frequency = self._extract_from_config(config, 'frequency')
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

    def new_post(self):
        """Create a brand new Post.
        
        :return: A string (which will be converted into a Post),
        a Post, or a list of Posts.
        """
        raise NotImplementedError()
    
    
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


class TextGeneratorBot(Bot):
    """A bot that comes up with a new piece of text every time it's invoked.
    """
    def new_post(self):
        """Create a brand new Post.

        :return: Some text.
        """
        return self.generate_text()
        
    def generate_text(self):
        raise NotImplementedError()


class Publisher(object):

    """A way of publishing the output of a bot."""

    @classmethod
    def from_config(cls, bot, module, full_config):
        publish_config = full_config.get('publish', {})
        module_config = publish_config.get(module)
        if not module_config:
            module_config = {}
        else:
            [module_config] = module_config
        
        publisher_module = importlib.import_module("publish." + module)
        publisher_class = getattr(publisher_module, "Publisher", None)
        if not publisher_class:
            raise Exception(
                "Loaded module %s but could not find a class called Publisher inside." % bot_module
            )
        publisher = publisher_class(bot, full_config, module_config)
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
