import json
import random
import requests

from olipy.ia import Text
from botfriend.bot import BasicBot
from botfriend.model import Post

class JunkMailBot(BasicBot):

    COLLECTION = "tednelsonjunkmail"

    def update_state(self):
        cutoff = self.model.last_state_update_time
        old_state = self.model.json_state or []
        query = Text.recent("collection:%s" % self.COLLECTION, cutoff=cutoff)
        new_items = [x.identifier for x in query]
        all_items = set(old_state + new_items)
        return list(all_items)

    def new_post(self):
        # Choose a random identifier from the current state.
        identifier = random.choice(self.model.json_state)
        if not identifier:
            return None

        text = Text(identifier)
        title = text.metadata['title']
        page_num = random.randint(0, text.pages-1)
        reader_url = text.reader_url(page_num)
        image_url = text.image_url(page_num)

        # Create the post.
        text = "%s\n\n%s" % (title, reader_url)
        post,  is_new = Post.from_content(
            self.model, text, reuse_existing=False
        )

        # Attach the image.
        if not image_url:
            return None
        response = requests.get(image_url)
        media_type = response.headers['Content-Type']
        post.attach(media_type, content=response.content)
        return post

Bot = JunkMailBot
