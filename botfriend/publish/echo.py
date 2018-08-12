"""Delivery mechanism for botfriend that just prints the output."""
from nose.tools import set_trace
from botfriend.bot import Publisher

class EchoPublisher(Publisher):
    def __init__(self, service_name, bot, full_config, **config):
        pass

    def publish(self, post, publication):
        print post.content
        
Publisher = EchoPublisher
