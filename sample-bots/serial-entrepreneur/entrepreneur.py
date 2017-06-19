import os
import json
import random
from olipy.english import us_states
from olipy.randomness import WanderingMonsterTable

class Grammar(object):

    def __init__(self, choices, means):
        self.choices = choices
        self.means = means or {}

    def fill(self, tokens):
        chosen = set([])
        for token in tokens:
            c = None
            while c is None or c in chosen:
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

class NounPhraseGrammar(Grammar):
    
    def __init__(self):
        choices = {}
        means = {}
        dir = os.path.split(__file__)[0]
        for name, filename, mean in (
                ('abstract', 'abstract_nouns.txt', 0.20),
                ('concrete', 'concrete_nouns.txt', None),
                ('adjectival', 'adjectival_nouns.txt', 0.20),
                ('adjective', 'adjectives.txt', 0.20)
        ):
            path = os.path.join(dir, 'data', filename)
            choices[name] = [x.strip() for x in open(path)]
            means[name] = mean
        super(NounPhraseGrammar, self).__init__(choices, means)

    patterns = [
        ['abstract', 'concrete'],
        ['abstract', 'concrete', 'concrete'],
        ['concrete', 'concrete'],
        ['adjectival', 'concrete'],
        ['adjectival', 'concrete', 'concrete'],
        ['concrete', 'abstract', 'concrete'],
        ['adjective', 'concrete', 'concrete'],
        ['adjective', 'abstract', 'concrete'],
        ['adjective', 'concrete'],
                ]

class Product(object):

    def __init__(self, grammar, pattern = None):
        self.grammar = grammar
        self.pattern = pattern or random.choice(self.grammar.patterns)
        self._name = list(self._generate_name())

    def _generate_name(self):
        for word in self.grammar.fill(self.pattern):
            yield word[0].capitalize() + word[1:]

    @property
    def name(self):
        return " ".join(self._name)

class Announcements(WanderingMonsterTable):

    common = ["%(product)s",
              "%(product)s",
              "%(product)s!",
              "%(product)s?", 
              "%(product)s...",
              "%(product)s...\n%(variant)s...",
              "%(product)s or %(variant)s?",
              "%(product)s? %(variant)s?",
              ]

    uncommon = [
        "%(product)s... %(variant)s...? Just throwing some ideas around.",
        "%(product)s... or maybe %(variant)s...",
        "%(product)s or %(variant)s?",
        "%(product)s or %(variant)s? You decide this one.",
        "%(product)s... no, how about %(a_variant)s...",
        "Eureka! %(product)s!",
        "This one's a winner, folks... the %(product)s!",
        "My latest million dollar idea: the %(product)s",
        "My latest billion dollar idea: the %(product)s",
        "How about %(a_product)s?",
        "Got a good feeling about this one... %(product)s!",
        "Market research... would you buy %(a_product)s?",
        "%(product)s? What was I thinking?! %(variant)s!",
        "You can have this idea for free: %(product)s",
        "Just an idea... %(product)s",
        "Finally got a working prototype of the %(product)s.",
        "Not sure that I can get my %(product)s to the prototype stage...",
        "Not sure whether I should try for the %(product)s or the %(variant)s first.",
        "Can't decide whether to pursue the %(product)s or the %(variant)s.",
        "Hate to do this, but I've got to choose between my babies... %(product)s or %(product2)s?",
        "It's tough out there... consumers WANT %(a_product)s, but they NEED %(a_variant)s.",
        "Was doing some brainstorming and came up with the %(product)s.",
        "Not sure about this one: %(product)s. Let me know what you think.",
        "I hear the %(product)s is big right now... would consumers go for %(a_variant)s?",
        "I estimate a $%(number)s billion market for the %(product)s.",
        "I anticipate a lot of demand for my %(product)s.",
        "%(product)s? Why not %(a_variant)s?",
        "There's something not quite right about my %(product)s...",
        "Something's missing from my %(product)s...",
        "Something's missing from my %(product)s... maybe %(a_variant)s instead?",
        "My %(product)s flops, but %(innovator)s's %(variant)s is a big hit? %(annoyance)s",
        "I've seen successful startups built around less than my %(product)s.",
        ]

    rare = [
        "I don't think I'll ever be happy with my %(product)s...",
        "Got a meeting with some VCs to pitch my %(product)s!",
        "I'm afraid that my new %(product)s is cannibalizing sales of my %(variant)s.",
        "Can't believe that cheap knockoff %(product)s is outselling my %(variant)s!",
        "One day they'll frame the napkin that shows my original design for the %(product)s.",
        "The %(product)s may have been first to market, but my %(variant)s has what consumers really want.",
        "I forsee %(a_product)s in every home!",
        "I didn't sleep at all last night... too busy designing the %(product)s.",
        'Apparently I wrote this on a napkin yesterday: "%(product)s". What a strange idea.',
        "Giving up on the %(product)s. If you can make it work, you can have it.",
        "You'll see a lot of imitations, but just remember that mine was the original %(product)s.",
        "I think I could get on 'Shark Tank' with a product like the %(product)s.",
        "Lots of positive feedback on my %(product)s...",
        "Getting some negative feedback on my %(product)s...",
        "Getting mixed feedback on my %(product)s...",
        "I anticipate a lot of demand for my %(product)s, once I get the bugs worked out.",
        "A bonus idea for those less creative than me: why not %(a_product)s?",
        "I admit, the %(product)s was a bad idea. I've moved on to the %(variant)s.",
        "The %(product)s flopped in test markets... back to the drawing board.",
        "The %(product)s flopped in my %(state)s test market... back to the drawing board.",
        "I come up with a lot of ideas in the shower... like %(a_product)s.",
        "Not gonna lie, the %(product)s hasn't been moving lately.",
        "Turns out it's illegal to sell %(a_product)s in the state of %(state)s.",
        "I see now that the %(product)s was just a step on the road to my %(variant)s.",
        "They mocked my %(product)s, but I'll show them... with the %(variant)s!",
        "Getting a lot of buzz around the %(product)s... sure to be a winner!",
        "Okay, forget the %(product)s! I've just invented the %(product2)s!",
        "Introducing the %(product)s!",
        "I'm starting to think my %(product)s is just too similar to other products out there, like the %(variant)s.",
        "Getting funding for %(a_product)s is more difficult than you'd think...",
        "I got an order for %(a_product)s! Now I just have to build one!",
        "Making progress... I just filed for a patent on the %(product)s!",
        "Gotta switch to buy-one get-one on the %(product)s...",
        ]

    very_rare = [
        "I'll always remember my first invention... the %(product)s. Or was it the %(variant)s?",
        "Sometimes I think about Edison's famous %(product)s and I wonder... can my %(product2)s compare?",
        "Great, now I'm stuck with a garage full of my underperforming %(product)s.",
        "Tesla's %(product)s was ahead of its time, but the time might be right for my %(variant)s.",
        "I know it flopped in the '80s, but it might be time to give the %(product)s another shot.",
        "%(bigco)s was interested in my %(product)s, but the deal fell through.",
        "I was JUST about to perfect my %(product)s, and then I see %(a_variant)s at %(store)s!",
        "Am I to be remembered as the inventor of the %(product)s?",
        "Maybe a holiday sale will get the %(product)s moving again...",
        "I haven't sold a single %(product)s...",
        "I hear %(billionaire)s is working on %(a_product)s...",
        "Trying to price the materials on %(a_product)s...",
        "I heard the government suppressed research towards %(a_product)s... a little worried about my %(variant)s.",
        ]

    def __init__(self):
        super(Announcements, self).__init__(
            Announcements.common, Announcements.uncommon, 
            Announcements.rare, Announcements.very_rare)
        self.grammar = NounPhraseGrammar()

    def choice(self):

        _product = Product(self.grammar)
        product = _product.name
        if product[0] in 'AEIOaeio':
            a_product = "an %s" % product
        else:
            a_product = "a %s" % product
      
        variant = Product(self.grammar, _product.pattern)

        if random.randint(1,3) < 3:
            variant = variant._name[0] + " " + " ".join(_product._name[1:])
        else:
            variant = " ".join(_product._name[:-1]) + " " + variant._name[-1]
        if variant[0] in 'AEIOaeio':
            a_variant = "an %s" % variant
        else:
            a_variant = "a %s" % variant

        store = random.choice([
            "Wal-Mart", "K-Mart", "Target", "the grocery store",
            "the department store", "Sears"])

        billionaire = random.choice([
                "Jeff Bezos", "Larry Page",
                "Richard Branson", "Paul Allen", "Nathan Myhrvold"])

        bigco = random.choice(
            ["Microsoft", "Google", "Apple", "Intel", "Nestle", "Kraft",
             "Phillip Morris", "Amazon", "The government", "Facebook",
             "Zynga",
             "The state of %s" % random.choice(us_states),
             "Monsanto"])

        innovator = random.choice(
            ["Microsoft", "Google", "Facebook"])

        annoyance = random.choice(
            ["Aargh!", "Go figure!", "I just don't get it.",
             "So frustrating!", "WHY?!?!"])

        state = random.choice(us_states)
        number = random.randint(1,300)

        product2 = Product(self.grammar).name

        template = super(Announcements, self).choice()
        d = dict(
            product=product,
            a_product = a_product,
            a_variant=a_variant,
            variant=variant,
            product2=product2,
            store=store,
            billionaire=billionaire,
            bigco=bigco,
            state=state,
            innovator=innovator,
            annoyance=annoyance,
            number=number)
        return template % d

if __name__ == '__main__':
    a = Announcements()
    for i in range(50):
        print a.choice()
