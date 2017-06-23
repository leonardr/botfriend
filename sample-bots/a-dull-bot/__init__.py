from typewriter import Typewriter
from bot import TextGeneratorBot

class TypewriterBot(TextGeneratorBot):

    def generate_text(self):
        typewriter = Typewriter()
        return typewriter.type("All work and no play makes Jack a dull boy.")

Bot = TypewriterBot

