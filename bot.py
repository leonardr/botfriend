import importlib
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
    the part that deals with managing the archive and delivering the
    creative output to various services.
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
        publishers = self.config.get('publish', {})
        if not publishers:
            self.log.warn("Bot %s defines no publishers.", self.name)
        self.publishers = [
            Publisher.from_config(self, module, config)
            for module in publishers
        ]
        
    def new_post(self):
        """Come up with something cool.

        :return: A Post.
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

    def schedule_next_post(self):
        """Assume a post just happened and schedule .next_post_time 
        appropriately.
        """
    
class TextGeneratorBot(Bot):
    """A bot that comes up with a new piece of text every time it's invoked.
    """
    def new_post(self):
        content = self.generate_text()
        return self.model.create_post(content)
        
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
