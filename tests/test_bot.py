from nose.tools import (
    eq_,
    set_trace,
)
from . import DatabaseTest
from model import (
    Post,
)

class TestBot(DatabaseTest):
    
    def test_publishable_posts(self):
        bot = self._bot()

        eq_(False, bot.state_updated)

        # Since this bot has never posted, publishable_posts returns a
        # list containing a single new post.
        [new_post] = bot.publishable_posts
        assert isinstance(new_post, Post)
        eq_(new_post.content, bot.new_posts[0])

        # Bot.update_state() was called during publishable_posts.
        eq_(True, bot.state_updated)

        # publishable_posts 
        set_trace()
        pass
