from nose.tools import set_trace
from model import Post


class Bot(object):
    """Bot implements the creative part of a bot.

    This is as distinct from BotModel in model.py, which implements
    the part that deals with managing the archive and delivering the
    creative output to various services.
    """

    def __init__(self, model, config):
        self.model = model
        self.config = config
    
    def run(self):
        """Come up with something cool.

        :return: A Post.
        """
        raise NotImplementedError()


class TextGeneratorBot(Bot):
    """A bot that comes up with a new piece of text every time it's invoked.
    """
    def run(self):
        content = self.generate_text()
        return self.model.create_post(content)

    def generate_text(self):
        raise NotImplementedError()


class Publisher(object):

    """A way of publishing the output of a bot."""

    def __init__(self, bot):
        self.bot = bot

    def publish(self, post):
        """Publish the content of the given Post object."""
