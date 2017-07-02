import json

from bot import Bot
from model import Post

class DeathBot3000(Bot):

    special_numbers = [
        'n/a', 'retired', 'coach', 'staff', 'mascot', 'announcer', 'jeerleader'
    ]

    @classmethod
    def render(cls, name, number, added, team):
        """Render a line from input.json as text."""
        if not name or not name.strip():
            return None
        if team:
            position = "\nSkating for the %(team)s"
            if number:
                lower = number.lower()
                if lower == 'n/a':
                    position = "%(team)s"
                    number = ""
                elif lower == 'retired':
                    position = "Retired from the %(team)s"
                elif lower == 'coach':
                    position = "Coach of the %(team)s"
                    number = ""
                elif lower == 'mascot':
                    position = "Mascot for the %(team)s"
                    number = ""
                elif lower == 'announcer':
                    position = "Announcer for the %(team)s"
                    number = ""
                elif lower == 'staff':
                    position = 'Staff member for the %(team)s'
                    number = ""
                elif lower == 'ref':
                    position = 'Referee for the %(team)s'
                    number = ""
                elif lower == 'jeerleader':
                    position = 'Jeerleader for the %(team)s'
                    number = ""
                else:
                    position = "#%(number)s for the %(team)s"
                position = "\n" + position
        elif number:
            if number.lower() in cls.special_numbers:
                position = None
            else:
                position = " (#%(number)s)"
        else:
            position = None

        if position:
            position = position % dict(number=number, team=team)
            name = name + position
        return name

    def import_post(self, content):
        """:param content: In this case, `content` comes in as a JSON list
        which we need to render as text.
        """
        inputs = json.loads(content)
        text = self.render(*inputs)
        post = Post.from_content(self.model, text)
        import pdb; pdb.set_trace()
        return post

    
Bot = DeathBot3000
