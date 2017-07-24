from pdb import set_trace
from StringIO import StringIO
import csv
import json
import re
from bot import ScraperBot

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
        state = set(self.model.json_state or [])
        for name, (description, ref, notes) in sorted(data.items()):
            if name == 'Relation Name':
                # Not a real link relation.
                continue
            if name in state:
                # We already know about this one.
                continue
            # This one's new.
            yield self.format(name, description, ref, notes)
            state.add(name)
        self.model.state = json.dumps(sorted(state))

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
