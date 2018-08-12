# encoding: utf-8
import json
from nose.tools import set_trace
from bot import BasicBot
from model import (
    Post,
)

class PostcardBot(BasicBot):
    
    def post_to_publisher(self, publisher, post, publication):
        """The thing we post to Mastadon is significantly different from the
        thing we post to Twitter.
        """
        state = post.json_state
        info = state.get('postcard_information', {})
        
        tags = ['#%s' % tag for tag in info.get('tags', [])]
        tag_string = " ".join(tags)
        short_content = info.get('url', '') + " " + tag_string
        max_text_length = 490 - len(short_content)

        text = info.get('inscription') or info.get('postcard-back')
        if text:
            trimmed = text[:max_text_length]
            long_content = trimmed
            if trimmed != text:
                long_content += u'…'
            long_content += ' ' + short_content
        if publisher.service == 'twitter':
            publication.content = short_content
        else:
            publication.content = long_content
        return super(PostcardBot, self).post_to_publisher(
            publisher, post, publication
        )

Bot = PostcardBot


