from pdb import set_trace
import random
import string
from bot import TextGeneratorBot
from olipy.corpus import Corpus

# Requires `pip install PyDictionary`
from PyDictionary import PyDictionary

class SloganBot(TextGeneratorBot):

    BIO_TEMPLATE = "The Party's eternal slogans are your surest ally in the war against %s."
    
    def __init__(self, *args, **kwargs):
        super(SloganBot, self).__init__(*args, **kwargs)
        twitter = None
        only_twitter = "This bot publishes to Twitter and only Twitter."
        if len(self.publishers) != 1:
            raise Exception(only_twitter)
        [publisher] = self.publishers
        if publisher.service != 'twitter':
            raise Exception(only_twitter)
        self.twitter = publisher.api
        self.dictionary = PyDictionary()
        
    @property
    def slogan(self):
        if random.random() < 0.25:
            corpus = 'abstract_nouns'
        else:
            corpus = 'adjectives'
        data = Corpus.load(corpus)
        pairs = []
        while len(pairs) < 3:
            seed = random.choice(data)
            antonyms = self.dictionary.antonym(seed)
            if antonyms:
                antonym = random.choice(antonyms)
                pairs.append((seed, antonym))
        slogans = ["%s IS %s" % tuple(map(string.upper, x)) for x in pairs]
        return "\n".join(slogans)
        
    def generate_text(self):
        # Generate a new slogan.
        slogan = self.slogan

        # Reset the bio.
        bio = self.BIO_TEMPLATE % random.choice(["Eurasia", "Eastasia"])
        self.twitter.update_profile(description=bio)

        # Delete all previous tweets and records of same.        
        for tweet in self.twitter.user_timeline():
            self.twitter.destroy_status(tweet.id)
        for post in self.model.posts:
            self._db.delete(post)
            
        return slogan
        
Bot = SloganBot
