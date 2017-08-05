import datetime
from nose.tools import (
    eq_,
    set_trace,
)
from model import (
    _now
)
from . import DatabaseTest

class TestBotModel(DatabaseTest):

    def setup(self):
        super(TestBotModel, self).setup()
        self.now = _now()
        
        self.bot = self._botmodel()
        self.the_past = self.now - datetime.timedelta(days=1)
        self.the_future = self.now + datetime.timedelta(days=1)
    
    def test_ready_scheduled_posts(self):
        """BotModel.ready_scheduled_posts finds all the existing Post objects
        it is appropriate to post right now.
        """
        
        # These two Posts are scheduled, because they're in the
        # database, but they're not scheduled to be published at any
        # particular time.
        publish_whenever = self._post(self.bot, "whenever")
        publish_whenever_2 = self._post(self.bot, "whenever 2")

        # This post is scheduled for the future, so
        # ready_scheduled_posts will never find it.
        publish_later = self._post(self.bot, "publish later")
        publish_later.publish_at = self.the_future

        # This post was already published, so ready_scheduled_posts will
        # never find it.
        already_published = self._post(self.bot, "already published")
        publication = self._publication(botmodel=self.bot, post=already_published)
        
        # When the bot is ready to post (either because it has never
        # posted or because a post is overdue), the post that was
        # created first will be the result from ready_scheduled_posts.
        self.bot.next_post_time = None
        eq_([publish_whenever], self.bot.ready_scheduled_posts)
        
        self.bot.next_post_time = self.the_past
        eq_([publish_whenever], self.bot.ready_scheduled_posts)

        # When the bot is _not_ ready to post, ready_scheduled_posts will
        # return an empty list unless there are overdue posts.        
        self.bot.next_post_time = self.the_future
        eq_([], self.bot.ready_scheduled_posts)

        # When there are overdue posts, they are returned in the
        # order they were supposed to have been posted.
        self.bot.next_post_time = self.now
        publish_now = self._post(self.bot, "publish now", publish_at=self.now)
        overdue = self._post(self.bot, "overdue", publish_at=self.the_past)
        eq_([overdue, publish_now], self.bot.ready_scheduled_posts)

        # BotModel.scheduled finds all scheduled posts in the
        # order they will be posted.
        eq_([overdue, publish_now, publish_later,
             publish_whenever, publish_whenever_2], self.bot.scheduled)

    def test_recent_posts(self):
        past = self._post(
            self.bot, "posted a while ago", publish_at=self.the_past,
            published=True
        )
        present = self._post(
            self.bot, "posted just now", publish_at=self.now,
            published=True
        )
        failed_just_now = self._post(
            self.bot, "failed post just now", publish_at=self.now,
            published=True
        )
        [publication] = failed_just_now.publications
        publication.report_failure("argh")
        
        future = self._post(
            self.bot, "will post later", publish_at=self.the_future,
        )
        whenever = self._post(
            self.bot, "post whenever", publish_at=None,
        )

        # recent_posts() returns recently published posts in
        # reverse chronological order.
        #
        # By default, it does not include posts that could not be
        # published.
        eq_([present, past], self.bot.recent_posts().all())

        # But you can change that.
        assert failed_just_now in self.bot.recent_posts(
            require_success=False).all()

        # You can also limit it to posts published in the recent past.
        one_hour_ago = self.now - datetime.timedelta(seconds=3600)
        eq_([present], self.bot.recent_posts(published_after=one_hour_ago).all())

        # posted_after can be either a datetime or a number of days.
        eq_([present, past], self.bot.recent_posts(published_after=2).all())
