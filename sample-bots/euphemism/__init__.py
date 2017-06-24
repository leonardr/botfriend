from euphemism import Quote
from bot import TextGeneratorBot

class EuphemismBot(TextGeneratorBot):

    def generate_text(self):
        return Quote().choice()
   
Bot = EuphemismBot
