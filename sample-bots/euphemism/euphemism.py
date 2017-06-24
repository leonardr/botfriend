# encoding: utf-8

import os
import json
import random
from olipy.randomness import WanderingMonsterTable
from olipy.corpus import Corpus

countries = [x for x in Corpus.load("countries") if not ' ' in x]
us_states = Corpus.load("us_states")

class Grammar(object):

    def __init__(self, choices, means):
        self.choices = choices
        self.means = means or {}

    def fill(self, tokens):
        chosen = set([])
        for token in tokens:
            c = None
            while c is None or c in chosen:
                if token not in self.means:
                    # It's a literal.
                    c = token
                else:
                    mean = self.means.get(token, None)
                    c = self.choose(self.choices[token], mean)
            chosen.add(c)
            yield c
    
    def choose(self, choices, mean):
        if mean is None:
            return random.choice(choices)
        else:
            mean = len(choices) * mean
            v = None
            while v is None or v >= len(choices):
                v = int(random.expovariate(1.0/mean))
            return choices[v]


dir = os.path.split(__file__)[0]

class EuphemismGrammar(Grammar):

    assonance_chance = 0
    capitalize = False

    _means = {}
    _choices = {}
    for name, corpus_name, mean in (
        ('gerund', 'gerunds', 0.3),
        ('past', 'past_tense', 0.3),
        ('present', 'present_tense', 0.3),           
        ('noun', 'scribblenauts_words', None),
        ('adjective', 'adjectives', 0.20),
        ('city', 'large_cities', None),
        ):
        _choices[name] = Corpus.load(corpus_name)
        _means[name] = mean

    occupations = [x for x in Corpus.load("humans/occupations")
                   if x.count(' ') <= 1]
    _choices['occupation'] = occupations
    _means['occupation'] = None

    animals = [x for x in Corpus.load("animals/common")
                   if x.count(' ') <= 1]

    _choices['country'] = countries
    _means['country'] = None

    _choices['state'] = us_states
    _means['state'] = None

    def __init__(self):
        super(EuphemismGrammar, self).__init__(self._choices, self._means)

    def fill(self, tokens):
        is_assonant = random.random() <= self.assonance_chance
        assonant_letter = None
        chosen = set([])
        yield_a = False
        for token in tokens:
            c = None
            tries = 0
            add_to_chosen = True
            while c is None or c in chosen:
                if token not in self.means:
                    # It's a literal.
                    c = token
                    add_to_chosen = False
                else:
                    mean = self.means.get(token, None)
                    assonance_tries = 0
                    while (c is None or c in chosen or (assonant_letter and c[0] != assonant_letter)):
                        c = self.choose(self.choices[token], mean)
                        assonance_tries += 1
                        if assonance_tries > 10:
                            assonant_letter = None
                            break
                tries += 1
                if tries > 100:
                    import pdb; pdb.set_trace()
            if add_to_chosen:
                chosen.add(c)
            if is_assonant and not assonant_letter:
                assonant_letter = c[0].lower()
            if self.capitalize and not c[0].upper() == c[0]:
                c = c.capitalize()
            if c == 'a':
                yield_a = True
            else:
                if yield_a:
                    if c[0] in 'aeiouAEIOU':
                        yield 'an'
                    else:
                        yield 'a'
                    yield_a = False
                yield c
    

class Wanking(EuphemismGrammar):

    assonance_chance = 0.4
    
    patterns = [
        ['gerund', 'the', 'animal'],
        ['gerund', 'the', 'animal'],
        ['gerund', 'the', 'occupation'],
        ['gerund', 'the', 'adjective', 'animal'],
        ['gerund', 'the', 'adjective', 'noun'],
        ['gerund', 'the', 'noun'],
        ['gerund', 'the', 'noun'],
                ]

class Sexing(EuphemismGrammar):
    
    assonance_chance = 0.6

    patterns = [
        ['gerund', 'the', 'noun'],
        ['gerund', 'the', 'adjective', 'noun'],
                ]

class SexAct(EuphemismGrammar):
    assonance_chance = 0.5
    capitalize = True

    patterns = [
        ['city', 'noun'],
        ['city', 'noun'],
        ['state', 'noun'],
        ['country', 'noun'],
        ['adjective', 'noun'],
        ]

class Shitting(EuphemismGrammar):

    assonance_chance = 0.01

    patterns = [
        ['gerund', 'a', 'noun'],
                ]

class TakeAShit(EuphemismGrammar):
    
    assonance_chance = 0.01

    patterns = [
        ['present', 'a', 'noun'],
                ]

class Farted(EuphemismGrammar):

    assonance_chance = 0.05

    patterns = [
        ['past', 'a', 'noun'],
        ['past', 'the', 'noun'],
        ]

class Fart(EuphemismGrammar):

    assonance_chance = 0.05

    patterns = [
        ['present', 'a', 'noun'],
        ['present', 'the', 'noun'],
        ]

class Died(EuphemismGrammar):

    patterns = [
        ['past', 'the', 'adjective', 'noun'],
        ['past', 'the', 'adjective', 'noun'],
        ['past', 'the', 'adjective'],
        ['gone', 'adjective'],
        ]

class Die(EuphemismGrammar):

    patterns = [
        ['present', 'the', 'adjective', 'noun'],
        ['present', 'the', 'adjective', 'noun'],
        ['present', 'the', 'adjective'],
        ['go', 'adjective'],
        ]


class Quote(WanderingMonsterTable):
    
    common = [
        '%(Pronoun)s was "%(wanking)s," if you know what I mean.',
        'I can\'t believe you\'ve never heard it called "%(wanking)s"!',
        'They were "%(sexing)s," if you know what I mean.',
        'Let\'s just say they were "%(sexing)s," wink wink.',
        '"%(Wanking)s"? Are you serious?',
        'I\'ve always called it "%(euphemism)s."',
        "Excuse me, I have to go %(takeashit)s.",
        'I\'ve got to "%(takeashit)s," if you know what I mean.',
        '%(Phew)s! Who %(farted)s?',
        'What\'s wrong with simple, clear terms like "%(euphemism)s"?',
        ]
    uncommon = [
        'In high school I spent a lot of time "%(wanking)s."',
        'There\'s nothing unnatural about %(wanking)s; everyone does it.',
        'I walked in on them "%(sexing)s," if you can believe it.',
        'I never heard that one before... we always called it "%(wanking)s".',
        'I prefer the term "%(euphemism)s."',
        '%(Phew)s, who %(farted)s in here?',
        'Did someone %(fart)s in here?',
        "Hold that thought—I have to %(takeashit)s.",
        'Reminds me of the time I caught my roommate "%(wanking)s."',
        'When I was a kid we always called it "%(euphemism)s."',
        '%(Admonition)s "%(Euphemism)s," please.',
        'I walked in on them doing the %(sexact)s, if you can believe it.',
        'I guess the kids these days are calling it "%(sexing)s."',
        'Apparently the kids these days are calling it "the %(sexact)s."',
        ]
    rare = [
        'I guess I\'ve always had a lot of guilt around, uh, %(wanking)s.',
        "I dunno, kinda looks like you were %(wanking)s.",
        "What are you doing in there, %(wanking)s?",
        'I\'m hip, I\'m with it, I know you call it "%(wanking)s" now.',
        "You'd better not be %(wanking)s in there!",
        "Hey, quit %(wanking)s and pay attention!",
        'I hear in %(state)s they call it "%(euphemism)s."',
        'You know, in %(state)s they call it "%(euphemism)s."',
        'You know, in %(country)s they call it "%(euphemism)s."',
        'There we were, right in the middle of the %(sexact)s...',
        'I hear in %(country)s they call it "%(euphemism)s."',
        'It\'s more romantic in %(language)s... they say "%(sexing)s."',
        '%(Admonition)s Please use the polite term, "%(euphemism)s."',
        'I\'ll always remember my first time "%(sexing)s."',
        'I\'m afraid the old %(gender)s has, shall we say, %(died)s.',
        'I\'m so sorry. When did your %(relative)s, shall we say, "%(die)s"?',
        'Honestly, I\'ve never understood what "%(euphemism)s" refers to.',
        'I don\'t know what "%(euphemism)s" means, and I don\'t want to know.',
        "The %(sexact)s? Isn't that illegal in %(lots_of_states)s states?",
        ]
    very_rare = [
        'It smells like someone %(farted)s in here.',
        'When I was a teenager my primary hobby was "%(wanking)s."',
        '%(Parent)s walked in on me, uh, "%(wanking)s".',
        'You know newlyweds... always "%(sexing)s"!',
        'Freud spoke of the "primal scene", in which the child witnesses his parents %(sexing)s.',
        'Down south we call it "%(wanking)s."',
        'Open a window! It smells like someone %(farted)s!',
        'Honestly, calling it "%(sexing)s" just makes it sound dirtier than it is.',
        'Sorry about that... %(food_makes)s me "%(fart)s."',
        "Sure, I've heard of it, but I've never heard it called the %(sexact)s.",
        "You ever try the %(sexact)s? It's not as easy as it looks.",
        'We in the LDS Church are very concerned about the epidemic of "%(wanking)s" among the youth of this generation.',
        "I don't know what they do all day... sit around %(wanking)s, maybe.",
        "I didn't think I'd enjoy doing the %(sexact)s... until I tried it!",
        'At least take this pamphlet detailing the evils of "%(wanking)s"!',
        ]

    def __init__(self):
        super(Quote, self).__init__(
            Quote.common, Quote.uncommon, 
            Quote.rare, Quote.very_rare)

    def make(self, cls):
        return (" ".join(cls().fill(random.choice(cls.patterns)))).encode("utf8")

    def choice(self):
        wanking = self.make(Wanking)
        _Wanking = wanking.capitalize()
        sexing = self.make(Sexing)
        takeashit = self.make(TakeAShit)
        shitting = self.make(Shitting)
        farted = self.make(Farted)
        fart = self.make(Fart)
        died = self.make(Died)
        die = self.make(Die)
        sexact = self.make(SexAct)
        food_makes = random.choice(
            ["beans always make", "beans make", "rich food makes", 
             "cabbage makes"])
        lots_of_states = random.randint(12,49)
        Phew = random.choice(["Whew", "Phew", "Geez", "Wow", "Ugh"])
        euphemism = random.choice([wanking, sexing, shitting])
        Euphemism = euphemism.capitalize()
        Admonition = random.choice([
                "Would you mind using less vulgar language?",
                "Watch your tongue!",
                "Watch your mouth!",
                "Language!",
                "That is unspeakably crude!",
                "Would you please watch your language?",
                ])
        gender = random.choice(["man", "woman", "fellow", "gal"])
        relative = random.choice(["grandfather", "grandmother", "aunt", "uncle", "great-aunt", "great-uncle", "great-grandfather", "great-grandmother"])
        Parent = random.choice(["Mom", "Dad", "My mother", "My father"])
        Pronoun = random.choice(["He", "She"])
        state = random.choice(us_states)
        country = "the United States"
        while country == "the United States":
            country = random.choice(countries)

        language = "English"
        languages = Corpus.load("languages")
        while language == "English":
            language = random.choice(languages)

        template = super(Quote, self).choice()
        d = dict(
            wanking=wanking,
            Wanking=_Wanking,
            sexing=sexing,
            takeashit=takeashit,
            farted=farted,
            fart=fart,
            died=died,
            die=die,
            sexact=sexact,
            lots_of_states=lots_of_states,
            euphemism=euphemism,
            Euphemism=Euphemism,
            Admonition=Admonition,
            Phew=Phew,
            Parent=Parent,
            Pronoun=Pronoun,
            gender=gender,
            relative=relative,
            state=state,
            country=country,
            language=language,
            food_makes=food_makes,
            )
        return template % d
    
if __name__ == '__main__':
    a = Quote()
    for i in range(10000):
        print a.choice()
