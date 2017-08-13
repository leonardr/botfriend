# encoding: utf-8
"""Tumblr delivery mechanism for botfriend."""
import re
from nose.tools import set_trace
import pytumblr
import logging
from bot import Publisher

class TumblrPublisher(Publisher):
    def __init__(
            self, bot, full_config, kwargs
    ):
        for key in ['consumer_key', 'consumer_secret', 'access_token',
                    'access_token_secret', 'blog']:
            if not key in kwargs:
                raise ValueError(
                    "Missing required Tumblr configuration key %s" % key
                )

        self.api = pytumblr.TumblrRestClient(
            kwargs['consumer_key'], kwargs['consumer_secret'],
            kwargs['access_token'], kwargs['access_token_secret']
        )
        set_trace()
        self.tumblr_blog = kwargs['blog']

    def self_test(self):
        # Do something that will raise an exception if the credentials are invalid.
        # Return a string that will let the user know if they somehow gave
        # credentials to the wrong account.
        set_trace()
        dashboard = self.api.dashboard()
                
    def publish(self, post, publication):
        content = publication.content or post.content
        if post.attachments:
            # TODO: Not sure what to do when there are multiple
            # attachments.
            [attachment] = post.attachments
            i = content.rfind(' ', 0, 20)
            slug = content[:i]

            # Create the post.
            response = self.tumblr.create_photo(
                self.tumblr_blog, state="published", format="html",
                caption=content, slug=slug
            )

            # Get information about the post.
            publication.external_id = response['id']
            set_trace()
            response = self.tumblr.posts(self.tumblr_blog, id=response['id'])
            set_trace()        

Publisher = TumblrPublisher

