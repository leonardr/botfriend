import datetime
import feedparser
from feedgen.feed import FeedGenerator
from botfriend.feed import Converter
from botfriend.bot import Publisher
from botfriend.model import (
    Post,
    Bot,
)
from file import FileOutputPublisher

class PodcastPublisher(FileOutputPublisher):

    def __init__(
            self, bot, full_config, module_config
    ):
        super(PodcastPubliser, self).__init__(bot, full_config, module_config)
        self.url = module_config['url']
        self.description = module_config.get('description')
        self.archive_size = module_config.get('archive_size', 10)


    @classmethod
    def make_post(self, bot, title, media_url, description=None, 
                  media_type='audio/mpeg', id=None):
        """A helper to make Post objects compatible with 
        the PodcastPublisher.
        """
        if isinstance(bot, Bot):
            bot = bot.model
        id = id or media_url
        post = Post.for_external_key(bot_model, id)
        post.state = json.dumps(
            dict(
                id=id, title=title, description=description,
                media_url=media_url, media_type=media_type
            )
        )
        return post

    def publish(self, post, publication):
        """Publish a new podcast entry.

        :param post: A Post created with PodcastPublisher.make_post.
        """
        # Load or create the feed.
        if os.path.exists(self.path):
            feed = Converter(open(self.path))
        else:
            feed = FeedGenerator()
        feed.load_extension('podcast')

        # Set feed-level metadata.
        feed.title(self.name)
        feed.link(self.url)
        feed.description(self.description)
        feed.updated(datetime.datetime.utcnow())
        feed.generator("Botfriend")
        
        # Add one item.
        state = json.loads(post.state)
        item = feed.add_entry()
        item.id(post['id'])
        item.title(post['title'])
        item.description(post['description'])
        item.enclosure(post['url'], 0, post['media_type'])

        # Trim to archive_size items
        feed = feed[:self.archive_size]

        # Write the feed back out.
        fg.rss_file(self.path)
