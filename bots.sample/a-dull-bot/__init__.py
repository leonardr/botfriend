from olipy.typewriter import Typewriter
from olipy.integration import pad
from bot import TextGeneratorBot

class TypewriterBot(TextGeneratorBot):

    def generate_text(self):
        typewriter = Typewriter()
        text = typewriter.type("All work and no play makes Jack a dull boy.")
        return pad(text)
        
Bot = TypewriterBot

