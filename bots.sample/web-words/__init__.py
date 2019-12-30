import random
import re
from olipy import corpora
import requests
from botfriend.bot import TextGeneratorBot

class WebWords(TextGeneratorBot):
    """A bot that pulls random words from a random webpage."""

    def update_state(self):
        """Choose random domain names until we find one that hosts a web page
        larger than ten kilobytes.
        """
        new_state = None
        while not new_state:

            # Make up a random URL.
            word = random.choice(corpora.words.english_words['words'])
            domain = random.choice(["com", "net", "org"])
            url = "http://www.%s.%s/" % (word, domain)
            
            try:
                self.log.info("Trying to get new state from %s" % url)
                response = requests.get(url, timeout=5)
                potential_new_state = response.content
                if len(potential_new_state) < 1024 * 10:
                    # This is probably a generic domain parking page.
                    self.log.info("That was too small, trying again.")
                    continue
                new_state = response.content
                self.log.info("Success!")
            except Exception as e:
                self.log.info("That didn't work, trying again.")
        return new_state

    def generate_text(self):
        """Choose some words at random from a webpage."""
        webpage = self.model.state
       
        # Choose a random point in the web page that's not right at the end.
        total_size = len(webpage)
        near_the_end = int(total_size * 0.9)
        starting_point = random.randint(0, near_the_end)

        # Find some stuff in the webpage that looks like words, rather than HTML.
        some_words = re.compile("([A-Za-z\s]{10,})")
        match = some_words.search(webpage[starting_point:])

        if not match:
            # Because we didn't find anything, we're choosing not to post
            # anything right now.
            return None
        data = match.groups()[0].strip()
        return data

Bot = WebWords
