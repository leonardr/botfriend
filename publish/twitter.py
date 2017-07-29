# encoding: utf-8
"""Twitter delivery mechanism for botfriend."""
import re
import unicodedata
from nose.tools import set_trace
import tweepy
from bot import Publisher


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
        self.api.home_timeline(count=1)
        
    def twitter_safe(self, content):
        return _twitter_safe(content)
        
    def publish(self, post, publication):
        content = self.twitter_safe(post.content)
        # TODO: update_with_media would go here if there were attachments
        # on the Post.
        try:
            response = self.api.update_status(content)
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

