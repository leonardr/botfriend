"""Twitter delivery mechanism for botfriend."""
from nose.tools import set_trace
import tweepy
from bot import Publisher

class TwitterPublisher(Publisher):
    def __init__(
            self, bot, consumer_key, consumer_secret, access_token,
            access_token_secret, **kwargs
    ):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def publish(self, post, previous_attempt):
        set_trace()

        
Publisher = TwitterPublisher
