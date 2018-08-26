import datetime
import json
from nose.tools import (
    assert_raises,
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

    def test_undeliverable_posts(self):
        succeeded = self._post(
            self.bot, "succeeded", publish_at=self.the_past,
            published=True
        )

        failed_second = self._post(
            self.bot, "second to fail", publish_at=self.now,
            published=True
        )
        
        failed_first = self._post(
            self.bot, "first to fail", publish_at=self.the_past,
            published=True
        )

        [publication] = failed_first.publications
        publication.report_failure("argh")

        [publication] = failed_second.publications
        publication.report_failure("argh")

        # undeliverable_posts puts posts earlier in the list if they
        # failed earlier.
        eq_([failed_first, failed_second],
            self.bot.undeliverable_posts.all())

    def test_state(self):
        eq_(None, self.bot.last_state_update_time)
        
        # Any JSONable object can be stored as Bot.json_state.
        state = [1,2,3]
        self.bot.json_state = state

        updated_time = self.bot.last_state_update_time
        assert updated_time != None
        
        eq_(state, self.bot.json_state)
        eq_(json.dumps(state), self.bot.state)

        # You can also just store some random string as Bot.state, but
        # then you can't use Bot.json_state.
        self.bot.state = "Not JSON"
        assert_raises(ValueError, lambda: self.bot.json_state)

        # Bot.last_state_update_time is updated every time you
        # modify the state.
        second_updated_time = self.bot.last_state_update_time
        assert second_updated_time > updated_time
        
        def set():
            self.bot.json_state = object()
        assert_raises(TypeError, set)


    def test_backlog(self):
        # Any list full of JSONable objects can be stored as
        # BotModel.backlog.
        eq_([], self.bot.backlog)
        backlog = [1234]
        self.bot.backlog = backlog
        eq_(json.dumps(backlog), self.bot._backlog)
        eq_(backlog, self.bot.backlog)

        # You can't store some random JSONable object as Bot.backlog,
        # it has to be a list.
        def set():
            self.bot.backlog = "Not a list"
        assert_raises(ValueError, set)

        # BotModel.pop_backlog removes one item from the backlog.
        eq_(1234, self.bot.pop_backlog())
        eq_([], self.bot.backlog)
