import datetime
import random
from olipy.integration import pad
from bot import Bot
from model import (
    get_one_or_create,
    Post,
)
from scat import ScatGenerator

class MahnaMahna(Bot):

    @property
    def next_workday(self):
        """Return Monday, if it's currently the weekend, and
        today otherwise.
        """
        now = datetime.datetime.now()
        day = now.replace(hour=0, minute=0, second=0)
        while day.weekday() > 5:
            day += datetime.timedelta(days=1)
        return day
    
    def new_post(self):
        """Create six Posts representing this bot's activity for one day."""

        sg = ScatGenerator()
        posts = []
        workday = self.next_workday
        for i, hour in enumerate([9, 11, 13, 15, 16, 17]):
            post_at = workday.replace(hour=hour)
            if i < 2:
                mahna = "Mahna mahna."
                output = pad(mahna, len(mahna)+10)
            elif i == 3:
                # Start scatting.
                output = random.choice(["Mahna ", "Mah ", "Mahna mah"])
                output += sg.scat(40)
            elif i == 4:
                # Keep on scatting.
                output = sg.scat(50).capitalize()
            elif i == 5:
                # Trail off in confusion.
                output = (sg.scat(30).capitalize() + "...\n" +
                          sg.scat(10).capitalize() + "...")
                if random.randint(0,1) == 1:
                    output += "\n" + sg.scat(5).capitalize() + "..."
            post, is_new = get_one_or_create(
                self._db, Post, bot=self.model, date=post_at
            )
            post.content = output
            posts.append(post)
        return posts
            
Bot = MahnaMahna
