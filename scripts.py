from nose.tools import set_trace
from argparse import ArgumentParser
from config import Configuration
from model import (
    Post,
    TIME_FORMAT,
)


class Script(object):
    pass

class BotScript(Script):
    """A script that operates on one or more bots."""

    @classmethod
    def parser(cls):
        parser = ArgumentParser()
        parser.add_argument(
            '--config',
            help="Directory containing the botfriend database.",
            required=True,
        )
        parser.add_argument(
            '--bot', 
            help='Operate on this bot.',
            nargs='*'
        )
        return parser
    
    def __init__(self):
        parser = self.parser()
        self.args = parser.parse_args()
        self.config = Configuration.from_directory(self.args.config)

    def run(self):
        for model in self.config.bots:
            if self.args.bot and not any(x in self.args.bot for x in (model.name, model.implementation.module_name)):
                # We're processing specific bots, and this one isn't
                # mentioned.
                continue
            self.process_bot(model)

    def process_bot(self, bot_model):
        raise NotImplementedError()


class PostScript(BotScript):
    """Create a new post for one or all bots."""

    @classmethod
    def parser(cls):
        parser = BotScript.parser()
        parser.add_argument(
            '--dry-run',
            help="Show what would be posted, but don't post it or commit to the database.",
            action='store_true'
        )
        return parser
    
    def process_bot(self, bot_model):
        posts = bot_model.next_posts()
        if self.args.dry_run:
            print bot_model.name
            for post in posts:
                print post.content
                print "-" * 80
                return

        # We're doing this for real.
        for post in posts:
            for publication in post.publish():
                publication.post.bot.log.info(publication.display())
        self.config._db.commit()


class BacklogScript(BotScript):
    """Show the backlog for a bot."""

    @classmethod
    def parser(cls):
        parser = BotScript.parser()
        parser.add_argument(
            "--limit",
            help="Limit the number of backlog items shown.",
            type=int,
            default=None
        )
        return parser

    def process_bot(self, bot_model):
        backlog = bot_model.backlog
        count = backlog.count()
        if self.args.limit:
            max_i = self.args.limit - 1
        else:
            max_i = None
        if count:
            bot_model.log.info("%d items in backlog" % count)
            for i, post in enumerate(bot_model.backlog):
                if max_i is not None and i > max_i:
                    break
                if post.publish_at:
                    when_post = post.publish_at.strftime(TIME_FORMAT)
                elif i == 0:
                    when_post = bot_model.next_post_time.strftime(TIME_FORMAT)
                else:
                    when_post = "Unscheduled"
                bot_model.log.info("%s | %s" % (when_post, post.content))
        else:
            bot_model.log.info("No backlog")
        
# Load backlog from a file.
