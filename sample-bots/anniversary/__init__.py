# encoding: utf-8

from pdb import set_trace
import json
import os
import random
import re
import sys
from textblob import TextBlob
from bot import TextGeneratorBot
from olipy.randomness import WanderingMonsterTable
from olipy.corpus import Corpus
from olipy.wordfilter import is_blacklisted

class MaterialExtractor(object):
    """Takes a string that mentions a phrase like "made of x",
    and extracts x.
    """
    emoji = re.compile(u'['
                       u'\U0001F300-\U0001F64F'
                       u'\U0001F680-\U0001F6FF'
                       u'\u2600-\u26FF\u2700-\u27BF]+', 
                       re.UNICODE)

    non_word = re.compile("[^a-zA-Z- ]")
    stop_at = ["http", "https", "#", "/", " - ", " @", ' lol', ' smh', 'heh']

    @classmethod
    def extract_material(cls, string, query):
        """Try to find something in a string that resembles a material.

        e.g. in the string "This is made of win!", the material would
        be "win".
        """        
        tweet = cls.emoji.sub("", string)
        blob = TextBlob(string)

        # print query, string, "/".join(blob.noun_phrases)
        # Try to find a noun phrase that looks like a material.
        for noun_phrase in blob.noun_phrases:
            if cls.looks_like_material(string, query, noun_phrase):
                if noun_phrase.startswith('old '):
                    noun_phrase = noun_phrase[4:]
                return noun_phrase.lower()

        # That didn't work. Try to find a non-proper noun that looks like
        # a material.
        for word, tag in reversed(blob.tags):
            if (tag == 'NN' and len(word) >= 3
                and word.lower() == word
                and cls.looks_like_material(string, query, word)):
                return word

        # Nothing worked. We can't find a material in this string.
        return None

    @classmethod
    def looks_like_material(self, string, query, potential):
        """Does the given string look like a material we can use?"""
        if self.non_word.search(potential):
            # It contains non-word characters.
            return False
        if potential.upper() == potential:
            # It's in all caps.
            return False
        if any (x in potential for x in self.stop_at):
            # It contains a link or other deal-breaker string.
            return False
        if any(x in potential for x in u'\u201d\u201c"'):
            # It's got quotes in it, which means it's probably a
            # truncated quotation.
            return False
        try:
            expect = re.compile(query + "\s+" + potential)
        except Exception, e:
            # We can't even build the regular expression to search for it.
            return False
        if not expect.search(string):
            # It doesn't immediately follow the string we were searching for.
            return False
        return True


class StateManager(object):
    """Manage the internal state of this bot, which contains materials
    periodically derived from Twitter searches.
    """
    
    # Strings that frequently precede materials.
    QUERIES = ['made out of', 'made entirely of', 'made from', 'made of', 'made from a', 'made of a', 'made from an', 'made of an', 'made out of an', 'made out of a', 'made of the', 'made from the', 'made out of the']
    
    def __init__(self, log, twitter, current_state):
        self.log = log
        self.twitter = twitter
        self.current_state = current_state
        if not isinstance(self.current_state, dict):
            self.current_state = {}

    def update(self):
        """Search the Internet for strings that appear to be materials.
        Store them in self.current_state.
        """
        self.current_state['twitter'] = self.update_twitter()

    def update_twitter(self):
        materials = set()
        for query in self.QUERIES:
            quoted = '"%s"' % query
            for tweet in self.twitter.search(q=quoted):
                text = tweet.text
                if is_blacklisted(text):
                    # If any part of the original tweet is blacklisted, don't
                    # take the risk of using part of it.
                    continue
                material = MaterialExtractor.extract_material(text, query)
                if material:
                    materials.add(material)
        return list(materials)

class Advisor(object):
    """Has lots of advice about anniversary presents.
    """

    COMMON = [
        u"%(nth)s anniversary - %(Material)s",
        u"%(nth)s anniverary - %(Material)s (traditional), %(Material2)s (modern)",
        u"%(nth)s anniversary - %(Material)s",
        u"%(nth)s anniverary - %(Material)s (traditional), %(Material2)s (modern)",
        u"%(Material)s - the traditional gift for the %(nth)s anniversary",
        u"%(Material)s - the modern gift for the %(nth)s anniversary",
        u"The modern %(nth)s anniversary gift: %(material)s",
        u"The traditional %(nth)s anniversary gift: %(material)s",
        u'The %(nth)s is the "%(material)s" anniversary.',
    ]

    UNCOMMON = [
        u"Traditionally, one gives %(material)s for the %(nth)s anniversary.",
        u'The %(nth)s has always been the "%(material)s" anniversary.',
        u"For the %(nth)s anniversary, it's %(material)s.",
        u"For the %(nth)s anniversary, it's got to be %(material)s.",
        u'Remember, the %(nth)s is the "%(material)s" anniversary.',
        u"It's your %(nth)s… say it with %(material)s.",
        u"%(Material)s for the %(nth)s… how romantic!",
        u"Make your %(nth)s anniversary special… give %(material)s.",
        u"%(Material)s? That's a bit old-fashioned. For your %(nth)s, consider %(material2)s instead.",
        u"For the %(nth)s, there's no better gift than %(material)s.",
        u"For your %(nth)s, a symbol of your enduring love: %(material)s.",
        u"I don't need any fancy %(material)s for our %(nth)s… simple %(material2)s will do.",
        u"%(He)s just couldn't wait… %(he)s gave me %(material)s for our %(nth)s anniversary instead of our %(next_one)s!",
        u"Why settle for less? Give genuine %(material)s for your %(nth)s anniversary.",
        u"%(Material)s - the perfect gift for your %(nth)s anniversary!",
    ]
    
    RARE = [
        u"As long as there have been marriages, %(nth)s anniversaries have been celebrated with %(material)s.",
        u"Can you believe %(he)s gave me %(material)s for our %(nth)s instead of %(material2)s?",
        u"For your %(nth)s, consider %(material)s as an ethical alternative to %(material2)s.",
        u"The only appropriate gift for the %(nth)s anniversary is %(material)s.",
        u"A good practical gift for the %(nth)s anniversary is %(material)s.",
        u"I've never understood why %(material)s is given for the %(nth)s... doesn't %(material2)s make more sense?",
        u"I'm trying to find %(material)s for our %(nth)s, but it's so expensive!",
        u"It's your %(nth)s anniversary. Show that you love %(him)s… with %(material)s.",
        u"The %(nth)s anniversary was once for %(material)s, but more and more couples are giving %(material2)s.",
        u"I'll never understand why the %(nth)s is the \"%(material)s\" anniversary…",
        u"%(Material)s for your %(nth)s… because %(hes)s worth it.",
        u"Is it old-fashioned to still expect %(material)s for your %(nth)s anniversary?",
        u"No, you've got it mixed up. You give %(material)s for the %(nth)s, and %(material2)s for the %(next_one)s.",
    ]

    VERY_RARE = [
        u"Call me old fashioned, but for my %(nth)s anniversary I'd better be getting %(material)s!",
        u"%(He)s won't say it, but for your %(nth)s, %(hes)s expecting %(material)s.",
        u"If your %(nth)s anniversary is coming up, you'd better start shopping for %(material)s.",
        u"%(Material)s? For the %(nth)s anniversary? Everyone knows it's %(material2)s!",
        u"Frankly, I'd be insulted if I didn't get %(material)s for my %(nth)s anniversary.",
        u"I got the greatest %(material)s for my %(nth)s!",
        u"I don't care what %(he)s gives me for our %(nth)s, so long as it's %(material)s!", 
        u"In my family, we give %(material)s for the %(nth)s instead of %(material2)s.",
        u"%(Material)s for your %(nth)s… isn't %(hes)s worth it?",
        u"If I don't get %(material)s for my %(nth)s, there won't be a %(next_one)s.",
        u"Sure, I'll be buying %(material)s for the %(nth)s, but the price has to be right.",
        u"The perfect %(nth)s anniversary… a romantic dinner and a gift of %(material)s.",
    ]
    
    def __init__(self, internal_state):
        self.messages = WanderingMonsterTable()
        self.messages.common = self.COMMON
        self.messages.uncommon = self.UNCOMMON
        self.messages.rare = self.RARE
        self.messages.very_rare = self.VERY_RARE
        self.materials = self.setup_materials(internal_state)
        
    def setup_materials(self, internal_state):
        """Build a WanderingMonsterTable of materials from different sources.
        """

        def load_local(x):
            """Load a data file from bot-specific storage 
            rather than through Corpus.
            """
            base_dir = os.path.split(__file__)[0]
            path = os.path.join(base_dir, "data", x)
            return [x.strip().decode("utf8") for x in open(path)]
                    
        exclude = set(load_local("real_life.txt"))
        def filter_materials(materials):
            """Exclude materials that are actually used as anniversary gifts."""
            return [x for x in materials if x and x.lower() not in exclude]

        def filtered_local(filename):
            """Combine load_local and filter_materials."""
            return filter_materials(load_local(filename))
        
        dwarf_fortress_materials = filtered_local("dwarf_fortress.txt")
        moma_materials = filtered_local("moma.txt")
        gutenberg_materials = filtered_local("gutenberg.txt")

        scribblenauts_words = filter_materials(
            Corpus.load("scribblenauts_words")
        )
        concrete_nouns = filter_materials(Corpus.load("concrete_nouns"))
        
        # Put all the materials in corpus into one big list.
        corpora_materials = []
        for corpus in (
                'abridged-body-fluids',
                'building-materials',
                'carbon-allotropes',
                'decorative-stones',
                'decorative-stones',
                'fabrics',
                'fibers',
                'gemstones',
                'layperson-metals',
                'metals',
                'natural-materials',
                'packaging',
                'plastic-brands',
                'sculpture-materials',
                'technical-fabrics'):
            corpora_materials.extend(filter_materials(Corpus.load(corpus)))

        # Unlike the other lists of materials, we need to do some
        # minimal processing here.
        seen_minecraft = set()
        for i in load_local("minecraft.txt"):
            material = i.strip()
            if '(' in material:
                paren = material.index('(')
                material = material[:paren]
            material = material.strip().lower()
            seen_minecraft.add(material)
        minecraft_materials = filter_materials(sorted(seen_minecraft))

        # Add materials obtained by semi-real-time searches of
        # data sources such as Twitter. 
        external_materials = set()
        if internal_state:
            for source, materials in internal_state.items():
                external_materials.update(filter_materials(materials))
        external_materials = list(external_materials)

        m = WanderingMonsterTable()
        if external_materials:
            m.common.append(list(external_materials))
        m.common.append(gutenberg_materials)
        m.uncommon.append(moma_materials)
        m.uncommon.append(corpora_materials)
        m.rare.append(scribblenauts_words)
        m.rare.append(concrete_nouns)
        m.rare.append(dwarf_fortress_materials)
        m.very_rare.append(minecraft_materials)
        return m
        
    def ordinal(self, x):
        x = int(x)
        if x == 11:
            return '11th'
        if x == 12:
            return '12th'
        if x == 13:
            return '13th'
        m = x % 10
        if m == 1:
            t = "%sst"
        elif m == 2:
            t = "%snd"
        elif m == 3:
            t = "%srd"
        else:
            t = "%sth"
        return t % x

    def number(self):
        x = 0
        while x < 1:
            x = random.randint(1,5)
            if x == 1:
                x = random.gauss(5,2)
            elif x == 2:
                x = random.gauss(10, 5)
            elif x == 3:
                x = random.gauss(20, 5)
            elif x == 4:
                x = random.gauss(30, 5)
            elif x == 5:
                x = random.gauss(40, 20)
        return int(x)

    def choose2(self, m):
        """Call m() until it gives two different choices. Return them both."""
        choice1 = m()
        choice2 = choice1
        while choice2 == choice1:
            choice2 = m()
        return choice1, choice2

    @property
    def pronoun(self):
        """Choose a random gendered pronoun and associated words."""
        if random.randint(1,2) == 1:
            return "He", "he", "he's", "him"
        else:
            return "She", "she", "she's", "her"

    def choose(self):
        """Advise as to an anniversary present."""
        # Choose a list to get materials from.
        list = self.materials.choice()
        material1 = random.choice(list)
            
        # 20% of the time, choose the second material from a
        # totally different list. Otherwise, choose a different
        # material from the same list.
        if random.random() >= 0.8:
            list = self.materials.choice()
        material2 = None
        while not material2 or material2 == material1:
            material2 = random.choice(list)

        number1, number2 = self.choose2(self.number)
        next_anniversary = self.ordinal(number1 + 1)
        number1 = self.ordinal(number1)
        number2 = self.ordinal(number2)

        He, he, hes, him = self.pronoun
        message = self.messages.choice()
        vars = dict(
            He = He,
            he = he,
            hes = hes,
            him = him,
            nth = number1,
            mth = number2,
            next_one = next_anniversary,
            material = material1,
            material2 = material2,
            Material = material1.capitalize(),
            Material2 = material2.capitalize(),
        )

        return message % vars

        
class AnniversaryBot(TextGeneratorBot):

    def __init__(self, *args, **kwargs):
        super(AnniversaryBot, self).__init__(*args, **kwargs)
        twitter = None
        for publisher in self.publishers:
            if publisher.service == 'twitter':
                twitter = publisher
                self.state_manager = StateManager(
                    self.log, twitter.api, self.model.json_state
                )
            
    def update_state(self):
        if self.state_manager:
            self.state_manager.update()
            return json.dumps(self.state_manager.current_state)
        else:
            self.log.warn("No Twitter publisher configured, cannot find materials from Twitter.")

    def generate_text(self):
        self.advisor = Advisor(self.model.json_state)

        text = None
        while not text or len(text) > 140:
            text = self.advisor.choose()
        return text

    def stress_test(self, runs):
        """The default implementation of stress_test() will work, but we
        implement our own method to avoid creating a ton of Advisor
        objects.
        """
        advisor = Advisor(self.model.json_state)
        for i in range(runs):
            print advisor.choose()
    
Bot = AnniversaryBot
