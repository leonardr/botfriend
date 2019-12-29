import random
from botfriend.bot import TextGeneratorBot

class NumberJokes(TextGeneratorBot):

    def generate_text(self):
        """Tell a joke about numbers."""
        num = random.randint(1,10)
        arguments = dict(
            num=num,
            plus_1=num+1,
            plus_3=num+3
        )
        setup = "Why is %(num)d afraid of %(plus_1)d? "
        punchline = "Because %(plus_1)d ate %(plus_3)d!"
        return (setup + punchline) % arguments

Bot = NumberJokes
