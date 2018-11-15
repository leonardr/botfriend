from dateutil import parser
from pdb import set_trace
import random

from olipy.ia import Audio

from botfriend.bot import BasicBot 
from botfriend.publish.podcast import PodcastPublisher

class PodcastBot(BasicBot):

    COLLECTION = "podcasts"

    def update_state(self):
        # Grab the 100 most recently posted podcasts.
        query = Audio.recent("collection:%s" % self.COLLECTION)
        max_count = 100
        choices = []
        a = 0
        for audio in query:
            choices.append(audio.identifier)
            a += 1
            if a >= max_count:
                break
        self.model.json_state = choices

    def file(self, item, format_name):
        """Find a file in a specific format."""
        for f in item.files:
            if f.format == format_name:
                return f
        return None
                
    def new_post(self):
        podcast = random.choice(self.model.json_state)
        podcast = Audio(podcast)
        meta = podcast.metadata

        mp3 = self.file(podcast, "VBR MP3")
        if not mp3:
            # This isn't really a podcast.
            return None
        title = meta.get('title')
        date = parser.parse(
            meta.get('date') or meta.get('publicdate')
        ).strftime("%d %b %Y")
        description = meta.get('description')
        creator = meta.get('creator')
        
        description = '<p>Originally published by %(creator)s on %(date)s.</p>%(description)s'
        description = summary % dict(
            title=title,
            description=description,
            date=date,
            creator=creator
        )
        # Create a post compatible with the PodcastPublisher.
        post, is_new = PodcastPublisher.make_post(
            self.model, title, mp3.url, description,
        )
        return post

Bot = PodcastBot
