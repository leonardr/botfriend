"""A publisher that just writes output to a file.

Useful mainly for testing.
"""
import os
from bot import Publisher
from nose.tools import set_trace

class FileOutputPublisher(Publisher):
    def __init__(
            self, bot, full_config, module_config
    ):
        filename = module_config['filename']
        if not filename.startswith(os.path.sep):
            filename = os.path.join(bot.directory, filename)
        self.path = filename
        dir, ignore = os.path.split(self.path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        
    def publish(self, post, publication):
        output = post.publish_at.strftime("%Y-%m-%d %H:%M:%S")
        output = output + " | " + post.content.encode("utf8") + "\n"
        with open(self.path, 'a') as out:
            out.write(output)
        publication.report_success()
        
Publisher = FileOutputPublisher
