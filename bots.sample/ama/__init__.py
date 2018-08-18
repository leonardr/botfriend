from pdb import set_trace
import json
import os
import random
import re
import sys
from textblob import TextBlob
from botfriend.bot import TextGeneratorBot
from olipy import corpora
from wordfilter import blacklisted

class IAMAExtractor(object):
    re_parts = [
        "[^.]+[!.] [^.]+[!.]",
        "[^.]+[!.\n]",
        "[^.!]+$",
    ]

    emoji = re.compile(u'['
                       u'\U0001F300-\U0001F64F'
                       u'\U0001F680-\U0001F6FF'
                       u'\u2600-\u26FF\u2700-\u27BF]+', 
                       re.UNICODE)

    stop_at = ["http", "#", "/", " - ", " @"]

    ends_with_alphanumeric = re.compile("\w$")

    single_quote_not_next_to_letter = [
        re.compile("[^a-zA-Z]'", re.I),
        re.compile("'[^a-zA-Z]", re.I)
    ]

    @classmethod
    def extract_iama(cls, text, query):
        """Extract the part of a sentence that looks like the start of an AMA."""
        for quality, p in enumerate(cls.re_parts):
            quality = len(cls.re_parts) - quality
            r = re.compile(r"\b(%s %s)" % (query, p), re.I + re.M)
            text = cls.emoji.sub("", text)
            m = r.search(text)
            if not m:
                continue
            match = m.groups()[0]
            for stop_at in cls.stop_at:
                index = match.find(stop_at)
                if index != -1:
                    match = match[:index]
            match = match.strip()
            if cls.ends_with_alphanumeric.search(match):
                match = match + "."
            if u'\u201d' in match or u'\u201c' in match or '"' in match:
                continue
            for i in cls.single_quote_not_next_to_letter:
                if i.search(match):
                    return None

            # A potential choice must be at least four words long.
            blob = TextBlob(match)
            if len(blob.tags) < 4:
                return None
                
            #print "%s <- %s" % (match, text)
            # print match.encode("utf8")
            return quality, match

        # Sometimes the problem is you searched for "I am x" and
        # Twitter returned "I'm x".
        if "I am" in query and "I'm" in text:
           return cls.extract_iama(
                text.replace("I am", "I'm"),
                query.replace("I am", "I'm"))

    @classmethod
    def has_bad_end(cls, s):
        """We don't want an AMA to end in what appears to be the middle of a sentence."""
        s = s.lower()
        for i in (' a', 'the', 'an'):
            if s.endswith(i+"."):
                return True
        return False


class StateManager(object):
    """Manage the internal state of IAMABot."""
    
    def __init__(self, log, twitter, state, max_potentials=1000):
        """:param twitter: A Twitter client. Used to search for usable phrases.

        :param state: The state object kept by the IAmABot's BotModel.
        This is a dictionary containing 'update' (the time the corpus
        was last refreshed) and 'potentials', a list of
        dictionaries. Each dictionary has keys 'content' (original tweet) and
        'ama' (the suggested AMA post derived from it).

        :param corpus_size: Keep track of this number of potential phrases.
        """
        self.log = log
        self.twitter = twitter
        self.potentials = state or []
        if self.potentials:
            self.already_seen = set(x['content'] for x in self.potentials)
        else:
            self.already_seen = set()
        self.max_potentials = max_potentials

    def update(self):
        """Search Twitter for phrases that can be reused. Add them
        to the bot state.
        """
        add_to_corpus = []

        # In addition to searching for phrases like "I am a", we're
        # going to pick a past tense verb like "accomplished" and
        # search for (e.g.) "I accomplished".
        past_tense = corpora.words.common_verbs["past_tense"]
        verb_of_the_day = random.choice(past_tense)
        random_verb = "I %s" % verb_of_the_day
        self.log.info("Today's random verb: '%s'", random_verb)

        for query in ["I am a", "I am an", "I am the", random_verb]:
            for data in self.query_twitter(query):
                    self.potentials.append(data)
                    self.log.info("Considering %r" % data)
                    
        # Cut off old potentials so the state doesn't grow without bounds.
        self.potentials = self.potentials[-self.max_potentials:]

    def query_twitter(self, query):
        """Search Twitter for a phrase and return an object
        for each tweet that could be reformatted as an AMA.
        """
        if not self.twitter:
            return
        quoted = '"%s"' % query
        results = self.twitter.search(q=quoted)
        for tweet in results:
            text = tweet.text
            if text in self.already_seen:
                # Ignore this; we already have it as a potential.
                continue
            self.already_seen.add(text)
            if blacklisted(text):
                continue
            if 'AMA' in text or 'ask me anything' in text.lower():
                # Don't use an actual AMA or AMA joke.
                continue
            iama = IAMAExtractor.extract_iama(text, query)
            if not iama:
                # We couldn't actually turn this into an AMA lead-in.
                continue
            score, iama = iama
            yield dict(
                content=text, query=query,
                iama=iama, score=score
            )
        
    def choose(self, recently_used_posts, recently_seen_words):
        """Make a weighted choice from potentials that are not
        in recently_used_posts and don't include a word in
        recently_seen_words.
        """
        possibilities = []
        for item in self.potentials:
            content = item['content']
            iama = item['iama'].lower()
            if any([iama in x for x in recently_used_posts]):
                continue
            words = set(word for word, tag in TextBlob(content.lower()).tags)
            if recently_seen_words.intersection(words):
                self.log.info("Ignoring due to recently seen word: '%s'", content)
                continue
            
            for i in range(item['score']):
                # Matches more likely to get a good result get weighted
                # more heavily.
                possibilities.append(item)
        if possibilities:
            return random.choice(possibilities)
        else:
            if recently_seen_words:
                return self.choose(recently_used_posts, set())
            else:
                if recently_seen_words or recently_used_posts:
                    return self.choose(set(), set())
                else:
                    self.log.error("Can't do anything -- no data to work from.")


class IAmABot(TextGeneratorBot):

    def __init__(self, *args, **kwargs):
        super(IAmABot, self).__init__(*args, **kwargs)
        twitter = None
        for publisher in self.publishers:
            if publisher.service == 'twitter':
                twitter = publisher
                break
        else:
            self.log.error("No Twitter publisher configured, cannot update state.")
        if self.model.state:
            state = json.loads(self.model.state)
        else:
            state = []
        self.state_manager = StateManager(self.log, twitter.api, state)
        
    @property
    def recently_used_words(self):
        """Make a list of nouns, verbs, and adjectives used in recent posts."""
        whitelist = set(['ama', 'am', 'this', 'i', "i'm"])
        recent_words = set()
        recent_posts = self.model.recent_posts(7)
        for post in recent_posts:
            blob = TextBlob(post.content)
            for word, tag in blob.tags:
                word = word.lower()
                if (tag[0] in 'NJV' and tag != 'VBP' and word not in whitelist):
                    recent_words.add(word)
        return recent_words

    def update_state(self):
        self.state_manager.update()
        return json.dumps(self.state_manager.potentials)
            
    def generate_text(self):        
        # We don't want to exactly repeat a post created in the past year.
        recent_posts = [x.content.lower() for x in self.model.recent_posts(365)]
        
        # We don't want to reuse a significant word in a post we created
        # in the past week.
        recent_words = self.recently_used_words

        ama = None        
        while not ama:
            choice = self.state_manager.choose(recent_posts, recent_words)
            if not choice:
                return None
            ama = choice['iama'] + " AMA" + random.choice('.. !')
            ama = ama.strip()
            if len(ama) > 140 or "\n" in ama or IAMAExtractor.has_bad_end(
                    ama
            ):
                ama = None
        self.log.info("The chosen one: %s", ama)
        return ama

Bot = IAmABot
