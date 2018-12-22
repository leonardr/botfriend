from pdb import set_trace
import datetime
import feedparser
import os
import json
import pytz

from feedgen.feed import FeedGenerator

from botfriend.bot import (
    Bot,
    Publisher,
)
from botfriend.feedbridge import Bridge
from botfriend.model import (
    Post,
)
from .file import FileOutputPublisher

class PodcastPublisher(FileOutputPublisher):

    def __init__(
            self, bot, full_config, module_config
    ):
        super(PodcastPublisher, self).__init__(bot, full_config, module_config)
        self.title = full_config['name']
        self.url = module_config['url']
        self.archive_size = module_config.get('archive_size', 10)
        self.description = module_config.get('description')

    @classmethod
    def make_post(self, bot, title, media_url, description=None, 
                  media_type='audio/mpeg', media_size=None, guid=None):
        """A helper to make Post objects compatible with 
        the PodcastPublisher.
        """
        if isinstance(bot, Bot):
            bot = bot.model
        guid = guid or media_url
        post, is_new = Post.for_external_key(bot, guid)
        post.content = guid
        post.state = json.dumps(
            dict(
                guid=guid, title=title, description=description,
                media_url=media_url, media_size=media_size,
                media_type=media_type
            )
        )
        return post, is_new

    def publish(self, post, publication):
        """Publish a new podcast entry.

        :param post: A Post created with PodcastPublisher.make_post.
        """
        # Load or create the feed.
        if os.path.exists(self.path):
            feed = Converter(open(self.path)).feed
        else:
            feed = FeedGenerator()
        feed.load_extension('podcast')

        # Set feed-level metadata.
        feed.title(self.title)
        feed.link(dict(href=self.url))
        feed.description(self.description)
        utc = pytz.timezone("UTC")
        now = utc.localize(datetime.datetime.utcnow())
        feed.updated(now)
        feed.generator("Botfriend")
        # Add one item.
        state = json.loads(post.state)
        item = feed.add_entry()
        guid = state['guid']
        is_permalink = any(guid.startswith(x) for x in ('http:', 'https:'))
        item.guid(state['guid'], is_permalink)
        item.title(state['title'])
        item.description(state['description'])
        item.enclosure(
            state['media_url'], 
            str(state.get('media_size', 0)),
            state['media_type']
        )
        item.published(now)
        item.updated(now)

        # Trim to archive_size items
        entries = feed._FeedGenerator__feed_entries
        while len(entries) > self.archive_size:
            # Remove old entries from consideration.
            entries.pop(-1)

        # Write the feed back out.
        feed.rss_file(self.path, pretty=True)
        publication.report_success()

Publisher = PodcastPublisher
