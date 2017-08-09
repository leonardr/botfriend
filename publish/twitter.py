# encoding: utf-8
"""Twitter delivery mechanism for botfriend."""
import re
import unicodedata
from nose.tools import set_trace
import tweepy
import logging
from bot import Publisher
logging.getLogger("tweepy.binder").setLevel(logging.WARN)

class TwitterPublisher(Publisher):
    def __init__(
            self, bot, full_config, kwargs
    ):
        for key in ['consumer_key', 'consumer_secret', 'access_token',
                    'access_token_secret']:
            if not key in kwargs:
                raise ValueError(
                    "Missing required Twitter configuration key %s" % key
                )
        auth = tweepy.OAuthHandler(kwargs['consumer_key'], kwargs['consumer_secret'])
        auth.set_access_token(kwargs['access_token'], kwargs['access_token_secret'])
        self.api = tweepy.API(auth)

    def self_test(self):
        # Do something that will raise an exception if the credentials are invalid.
        # Return a string that will let the user know if they somehow gave
        # credentials to the wrong account.
        return self.api.me().screen_name
        
    def twitter_safe(self, content):
        return _twitter_safe(content)
        
    def publish(self, post, publication):
        content = publication.content or post.content
        content = self.twitter_safe(content)
        arguments = dict(status=content)
        if post.attachments:
            # Looks like we can only add one attachment?
            # TODO: Try to find one we know is an image, since
            # only images are allowed.
            set_trace()
            attachment = post.attachments[0]
            method = self.api.update_with_media
            if attachment.filename:
                arguments = dict(filename=attachment.filename)
            else:
                arguments = dict(file=StringIO(attachment.content))
        else:
            # Just a regular tweet.
            method = self.api.update_status
        try:
            response = method(**arguments)
            publication.report_success()
        except tweepy.error.TweepError, e:
            publication.report_failure(e)

def _twitter_safe(content):
    """Turn a string into something that won't get rejected by Twitter."""
    content = unicode(content)
    content = unicodedata.normalize('NFC', content)
    for bad, replace in ('D', u'𝙳'), ('M', u'𝙼'):
        if any(content.startswith(x) for x in (bad + ' ', bad + '.')):
            content = re.compile("^%s" % bad).sub(replace, content)
            content = content.encode("utf8")
    return content[:140]

Publisher = TwitterPublisher

