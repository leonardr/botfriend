from euphemism import Quote
from botfriend.bot import TextGeneratorBot

class EuphemismBot(TextGeneratorBot):

    def generate_text(self):
        return Quote().choice()
   
Bot = EuphemismBot
