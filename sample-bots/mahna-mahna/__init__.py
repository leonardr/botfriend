import datetime
import random
from nose.tools import set_trace
from olipy.integration import pad
from bot import Bot
from model import (
    get_one_or_create,
    Post,
)
from scat import ScatGenerator

class MahnaMahna(Bot):

    def schedule_posts(self, filehandle):
        """Load five posts for the day if it's before 9AM on a weekday."""

        # Hard-coded UTC offset. :p
        utc_offset = datetime.timedelta(hours=5)
        now = datetime.datetime.utcnow()
        day = now.replace(hour=0, minute=0, second=0)
        if day.weekday() > 5:
            # It's the weekend. Do nothing.
            self.log.info("Taking the weekend off.")
            return
        if now.hour >= 9 + 5:
            # It's past 9 AM. Do nothing.
            self.log.info("Too late, it's past 9 AM.")
            return

        if self.model.scheduled:
            # There are already scheduled posts. do nothing.
            self.log.info("Not doing anything until scheduled posts are cleared out.")
            return

        sg = ScatGenerator()
        posts = []
        for i, hour in enumerate([9, 11, 13, 15, 16, 17]):
            publish_at = day.replace(hour=hour) + utc_offset
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
                self._db, Post, bot=self.model, publish_at=publish_at
            )
            post.content = output
            self.log.info("Will publish %s at %s", post.content, post.publish_at)
            posts.append(post)
        return posts
            
    def new_post(self):
        # We only publish posts scheduled in advance.
        pass
            
Bot = MahnaMahna
