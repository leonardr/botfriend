from entrepreneur import Announcements
from botfriend.bot import TextGeneratorBot

class EntrepreneurBot(TextGeneratorBot):

    def generate_text(self):
        return Announcements().choice()

Bot = EntrepreneurBot
