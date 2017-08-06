import datetime
from nose.tools import (
    assert_raises,
    eq_,
    set_trace,
)
from . import DatabaseTest
from bot import Bot
from model import (
    InvalidPost,
    Post,
    _now,
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

        # Since this bot has no state update schedule,
        # Bot.update_state() was not called.
        eq_(False, bot.state_updated)

        # Calling publishable_posts returns an empty list, since it's not yet
        # time for another post.
        eq_([], bot.publishable_posts)

    def test_publishable_posts_may_update_state(self):
        bot = self._bot(config=dict(state_update_schedule=1, schedule=1))
        eq_(True, bot.state_needs_update)
        bot.publishable_posts
        eq_(True, bot.state_updated)
        eq_(False, bot.state_needs_update)

    def test_backlog(self):
        bot = self._bot()
        eq_([], bot.backlog)
        item = {"k": "v"}

        # By default, items are stored in the backlog as is.
        eq_(item, bot.backlog_item(item))

        # Backlog items are transparently serialized and deserialized
        # to JSON.
        bot.extend_backlog([item])
        eq_([item], bot.backlog)

        bot.clear_backlog()
        eq_([], bot.backlog)

        
    def test_publishable_posts_pops_backlog(self):
        bot = self._bot()
        bot.extend_backlog(["backlog_1", "backlog_2"])
        [post1] = bot.publishable_posts
        eq_("backlog_1", post1.content)

        # There's still a backlog item, but it's not time for another post,
        # so publishable_posts doesn't pop it.
        eq_(["backlog_2"], bot.backlog)
        eq_([], bot.publishable_posts)

    def test_publishable_posts_returns_all_scheduled_posts(self):
        bot = self._bot()
        now = _now()
        yesterday = now - datetime.timedelta(days=1)
        day_before = now - datetime.timedelta(days=2)
        tomorrow = now + datetime.timedelta(days=1)
        publish_yesterday = self._post(
            bot.model, "yesterday", publish_at=yesterday
        )
        publish_earlier = self._post(
            bot.model, "day before", publish_at=day_before
        )
        publish_later = self._post(
            bot.model, "tomorrow", publish_at=tomorrow
        )

        # publishable_posts returns all posts that should have been
        # published by now.
        eq_([publish_earlier, publish_yesterday], bot.publishable_posts)

        # Since the scheduled posts weren't _created_ by the
        # publishable_posts, they don't go away when you call
        # publishable_posts once. They will stick around until they're
        # published.
        eq_([publish_earlier, publish_yesterday], bot.publishable_posts)

    def test_to_post_list(self):
        """Test the method that handles the output of new_post."""

        class ModifierBot(Bot):
            def object_to_post(self, obj):
                return obj + "!"

        bot = self._bot(ModifierBot)
        m = bot._to_post_list
        post = self._post()

        # A bot can turn an object (such as a backlog object) into a post
        # by creating the Post object, or a list of posts.
        eq_([post], m(post))
        eq_([post], m([post]))

        # A bot can also create a Post by defining object_to_post to
        # return a string.  publishable_posts takes care of actually
        # converting it into a post.
        [modified_post] = m("A string")
        assert isinstance(modified_post, Post)
        eq_("A string!", modified_post.content)

        # It's also okay for object_to_post to return the actual Post object.
        class PostBot(Bot):
            def object_to_post(self, obj):
                post, is_new = Post.from_content(self.model, obj)
                return post
        bot = self._bot(PostBot)
        [post] = bot._to_post_list("A string")
        assert isinstance(modified_post, Post)
        eq_("A string", post.content)

        # Or a list of Post objects.
        class PostBot(Bot):
            def object_to_post(self, obj):
                post, is_new = Post.from_content(self.model, obj)
                return [post]
        [post] = self._bot(PostBot)._to_post_list("A string")
        assert isinstance(modified_post, Post)
        eq_("A string", post.content)

        # No other type of value is acceptable.
        class PostBot(Bot):
            def object_to_list(self, obj):
                return dict(value=obj)
        assert_raises(
            InvalidPost, self._bot(PostBot)._to_post_list, ["A complicated value"]
        )
