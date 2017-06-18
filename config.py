from nose.tools import set_trace
import os
import logging
from model import production_session
logging.getLogger().setLevel(logging.INFO)
stderr_handler = logging.StreamHandler()
logging.getLogger().addHandler(stderr_handler)


class Configuration(object):
    """Encapsulates all configuration for a botbuddy installation."""

    def __init__(self, _db, bots):
        """Constructor.

        :param _db: A connection to the database.
        :param bots: A list of Bot objects.
        """
        self._db = _db
        self.bots = bots

    @classmethod
    def from_directory(cls, directory):
        """Load database and configuration from a directory on disk.

        The database is kept in `botbuddy.sqlite` and bots are found
        in subdirectories.
        """
        log = logging.getLogger("Loading configuration from %s" % directory)
        database_path = os.path.join(directory, 'botbuddy.sqlite')
        _db = production_session(database_path)
        bots = []
        for f in os.listdir(directory):
            p = os.path.join(directory, f)
            if os.path.isdir(p):
                log.info("Loading %s" % f)
                # It's a directory; does it contain a bot?
                expect = [os.path.join(directory, x)
                          for x in '__init__.py', 'bot.yaml']
                if all(os.path.exists(x) for x in expect):
                    bot = Bot.from_directory(_db, directory)
        return Configuration(_db, bots)
                
