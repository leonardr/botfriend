from olipy.typewriter import Typewriter
from olipy.alphabet import Alphabet
from botfriend.bot import TextGeneratorBot

def pad(s, destination_size=None):
    """Pad a string using different whitespace characters to stop Twitter
    from thinking two tweets are the same.
    Will try to add 10% whitespace to the string.
    """
    if not destination_size:
        destination_size = min(len(s) + max(len(s)*0.1, 5), 140)
    padding = ''
    for i in range(len(s), int(destination_size)):
        padding += Alphabet.random_whitespace()
    return s + padding

class TypewriterBot(TextGeneratorBot):

    def generate_text(self):
        typewriter = Typewriter()
        text = typewriter.type("All work and no play makes Jack a dull boy.")
        return pad(text)
        
Bot = TypewriterBot

