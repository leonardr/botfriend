import datetime
from nose.tools import (
    eq_,
    set_trace,
)
from model import (
    _now
)
from . import DatabaseTest

class TestBot(DatabaseTest):

    def test_ready_scheduled_posts(self):

        now = _now()
        
        bot = self._botmodel()
        the_past = now - datetime.timedelta(days=1)
        the_future = now + datetime.timedelta(days=1)

        # These two Posts are scheduled, because they're in the
        # database, but they're not scheduled to be published at any
        # particular time.
        publish_whenever = self._post(bot)
        publish_whenever_2 = self._post(bot)

        # This post is scheduled for the future, so
        # ready_scheduled_posts will never find it.
        publish_later = self._post(bot)
        publish_later.publish_at = the_future

        # This post was already published, so ready_scheduled_posts will
        # never find it.
        already_published = self._post(bot)
        publication = self._publication(botmodel=bot, post=already_published)
        
        # When the bot is ready to post (either because it has never
        # posted or because a post is overdue), the post that was
        # created first will be the result from ready_scheduled_posts.
        bot.next_post_time = None
        eq_([publish_whenever], bot.ready_scheduled_posts)
        
        bot.next_post_time = the_past
        eq_([publish_whenever], bot.ready_scheduled_posts)

        # When the bot is _not_ ready to post, ready_scheduled_posts will
        # return an empty list unless there are overdue posts.        
        bot.next_post_time = the_future
        eq_([], bot.ready_scheduled_posts)

        # When there are overdue posts, they are returned in the
        # order they were supposed to have been posted.
        bot.next_post_time = now
        publish_now = self._post(bot, publish_at=now)
        overdue = self._post(bot, publish_at=the_past)
        eq_([overdue, publish_now], bot.ready_scheduled_posts)
