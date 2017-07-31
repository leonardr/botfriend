from nose.tools import set_trace
from argparse import ArgumentParser
import sys
import time

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
        self.config = Configuration.from_directory(self.args.config, self.args.bot)

    def run(self):
        for model in self.config.bots:
            if self.args.bot and not any(x in self.args.bot for x in (model.name, model.implementation.module_name)):
                # We're processing specific bots, and this one isn't
                # mentioned.
                continue
            try:
                self.process_bot(model)
            except Exception, e:
                # Don't let this crash the whole script.
                model.implementation.log.error(e.message, exc_info=e)
        self.config._db.commit()
        
    def process_bot(self, bot_model):
        raise NotImplementedError()


class SingleBotScript(BotScript):
    """A script that _must_ be run against a single bot."""

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
            required=True
        )
        return parser

class RepublicationScript(BotScript):
    """Attempt to publish already created posts that failed in their
    delivery.
    """
    @classmethod
    def parser(cls):
        parser = BotScript.parser()
        parser.add_argument(
            "--limit",
            help="Limit the number of posts to republish per bot.",
            type=int,
            default=1
        )
        return parser
    
    def process_bot(self, bot_model):
        undelivered = bot_model.undeliverable_posts().limit(self.args.limit)
        for post in undelivered:
            for publication in post.publications:
                if not publication.error:
                    continue
                # Find the publisher responsible for this
                matches  = [x for x in bot_model.implementation.publishers
                            if x.service == publication.service]
                if not matches:
                    # This bot doesn't use this publisher anymore.
                    continue
                [publisher] = matches
                bot_model.log.info(
                    "Attempting to republish to %s: %s" % (
                        publication.service,
                        post.content
                    )
                )
                publisher.publish(post, publication)
                if publication.error:
                    bot_model.log.info("Failure: %s" % publication.error)
                else:
                    bot_model.log.info("Success!")


class DashboardScript(BotScript):
    """Display the current status of one or more bots."""
    def process_bot(self, bot_model):

        recent = bot_model.recent_posts().limit(1).all()
        if not recent:
            bot_model.log.info("Has never posted.")
        else:
            [recent] = recent
            bot_model.log.info("Most recent post: %s" % recent.content)
            for publication in recent.publications:
                if publication.error:
                    bot_model.log.info(
                        "%s ERROR: %s" % (publication.service, publication.error)
                    )
                else:
                    bot_model.log.info(
                        "%s posted at %s" % (publication.service,
                                             publication.most_recent_attempt
                        )
                    )
        
        backlog = bot_model.backlog
        count = backlog.count()
        next_post_time = None
        if count:
            if count == 1:
                item = "item"
            else:
                item = "items"
            bot_model.log.info("%d %s in backlog" % (count, item))
            next_item = backlog.limit(1).one()
            bot_model.log.info(
                "Next up: %s" % next_item.content
            )
            next_post_time = next_item.publish_at
        else:
            if bot_model.next_post_time:
                next_post_time = bot_model.next_post_time
        if next_post_time:
            bot_model.log.info(
                "Next post at %s" % next_post_time.strftime(TIME_FORMAT)
            )
        else:
            bot_model.log.info(
                "Next post not scheduled."
            )

            
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
        parser.add_argument(
            '--force',
            help="Post even if the scheduler would not normally post now.",
            action='store_true'
        )
        return parser
    
    def process_bot(self, bot_model):
        if self.args.force:
            bot_model.next_post_time = None

            # Start from scratch without any state.
            #from model import Session
            #_db = Session.object_session(bot_model)
            #for i in _db.query(Post).filter(Post.bot==bot_model):
            #print "Deleting %s" % i.content
            #_db.delete(i)
            bot_model.state = None
            bot_model.last_state_update_time = None
            #_db.commit()
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


class StateShowScript(BotScript):
    """Show the internal state for a bot."""

    def process_bot(self, bot_model):
        last_update = bot_model.last_state_update_time
        print "State for %s (last update %s)" % (bot_model.name, last_update)
        print bot_model.state
        

class StateRefreshScript(BotScript):
    """Refresh the internal state for a bot."""

    def process_bot(self, bot_model):
        bot_model.implementation.check_and_update_state(force=True)
        print "State for %s (last update %s)" % (
            bot_model.name, bot_model.last_state_update_time
        )
        print bot_model.state


class StressTestScript(BotScript):
    """Stress-test a bot's generative capabilities without posting anything."""

    @classmethod
    def parser(cls):
        parser = BotScript.parser()
        parser.add_argument(
            '--rounds',
            help="Run the bot's generator this many times. (Default is 10,000)",
            type=int,
            default=10000
        )
        return parser

    def process_bot(self, bot_model):
        bot_model.implementation.stress_test(self.args.rounds)

class PublisherTestScript(BotScript):
    """Verify  that a bot's publishers are functioning without posting anything."""

    def process_bot(self, bot_model):
        for publisher in bot_model.implementation.publishers:
            try:
                result = publisher.self_test() or ""
                print "GOOD %s %s %s" % (bot_model.name, publisher.service, result)
            except Exception, e:
                print "FAIL %s %s: %s" % (
                    bot_model.name, publisher.service, e
                )        
        
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
            if count == 1:
                item = "item"
            else:
                item = "items"
            bot_model.log.info("%d %s in backlog" % (count, item))
            for i, post in enumerate(bot_model.backlog):
                if max_i is not None and i > max_i:
                    break
                if post.publish_at:
                    when_post = post.publish_at.strftime(TIME_FORMAT)
                elif i == 0 and bot_model.next_post_time:
                    when_post = bot_model.next_post_time.strftime(TIME_FORMAT)
                else:
                    when_post = "Unscheduled"
                bot_model.log.info("%s | %s" % (when_post, post.content))
        else:
            bot_model.log.info("No backlog")


class BacklogLoadScript(SingleBotScript):

    @classmethod
    def parser(cls):
        parser = SingleBotScript.parser()
        parser.add_argument(
            "--limit",
            help="Limit the number of backlog items loaded.",
            type=int,
            default=None
        )
        parser.add_argument(
            "--file",
            help="Load from this file instead of standard input.",
            default=None
        )

        return parser

    def process_bot(self, bot_model):
        a = 0
        if self.args.file:
            fh = open(self.args.file)
        else:
            fh = sys.stdin
        for item in fh.readlines():
            post, is_new = bot_model.implementation.import_post(item.strip())
            if is_new:
                bot_model.log.info("Loaded: %r", post.content)
            else:
                bot_model.log.info("Already exists: %r", post.content)
                a += 1
            if self.args.limit and a >= self.args.limit:
                return


class BacklogClearScript(SingleBotScript):

    def process_bot(self, bot_model):
        backlog = list(bot_model.backlog)
        if not backlog:
            # Nothing to do
            return
        bot_model.log.warn("About to clear backlog for %s." % bot_model.name)
        bot_model.log.warn("Sleeping for 5 seconds to give you a chance to Ctrl-C.")
        time.sleep(1)
        for post in backlog:
            self.config._db.delete(post)
