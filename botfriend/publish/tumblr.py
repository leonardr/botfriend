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
        self.tumblr_blog = kwargs['blog']

    def self_test(self):
        # Do something that will raise an exception if the credentials are invalid.
        # Return a string that will let the user know if they somehow gave
        # credentials to the wrong account.
        info = self.api.info()
        for blog in info['user']['blogs']:
            if blog['name'] == self.tumblr_blog:
                return blog['title']
        raise ValueError(
            'Credentials are valid but could not find blog %s' % blog['name']
        )
                
    def publish(self, post, publication):
        content = publication.content or post.content        
        paths = [x.filename.encode("utf8") for x in post.attachments]

        i = post.content.rfind(' ', 0, 20)
        slug = post.content[:i]

        content = content.encode("utf8")
        slug = slug.encode("utf8")
        
        # Create the post.
        response = self.api.create_photo(
            self.tumblr_blog, state="published", format="html",
            caption=content, slug=slug, data=paths
        )

        # Set the post's external ID.
        publication.report_success(response['id'])

Publisher = TumblrPublisher

