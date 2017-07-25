from pdb import set_trace
from StringIO import StringIO
import csv
import json
import re
from bot import ScraperBot
from model import (
    Post,
)

class LinkRelationBot(ScraperBot):

    url = "http://www.iana.org/assignments/link-relations/link-relations-1.csv"

    link_re = re.compile("\[([^]]+)\]")
    compress_whitespace_re = re.compile("\s+")
    
    def to_dict(self, f):
        """Convert a CSV file to a dictionary."""
        d = {}
        reader = csv.reader(f)
        for name, description, ref, notes in reader:
            d[name] = [description, ref, notes]
        return d
    
    def scrape(self, response):
        data = self.to_dict(StringIO(response.content))

        # Grab the list of link relations we've already learned about.
        posts = []
        for name, (description, ref, notes) in sorted(data.items()):
            if name == 'Relation Name':
                # Not a real link relation.
                continue
            post, is_new = Post.for_external_key(self, name)
            if is_new:
                post.content = self.format(name, description, ref, notes)
                posts.append(post)
        return posts

    def format(self, name, description, ref, notes):
        description = description.decode("utf8")
        match = self.link_re.search(ref)
        link = ''
        if match:
            link = match.groups()[0]
            if link.startswith('RFC'):
                link = "http://tools.ietf.org/html/%s" % (link.lower())

        link_size = 20
        description = self.compress_whitespace_re.sub(" ", description).strip()
        return '"%s" (%s) %s' % (name, link, description)
        
Bot = LinkRelationBot
