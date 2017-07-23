from nose.tools import set_trace
import os
import sys
import logging
from model import (
    production_session,
    BotModel,
    TIME_FORMAT,
)

logging.basicConfig(
    level=logging.INFO,
    format="LOG %(asctime)s | %(name)s | %(message)s",
    datefmt=TIME_FORMAT,
)


class Configuration(object):
    """Encapsulates all configuration for a botfriend installation."""

    def __init__(self, _db, bots):
        """Constructor.

        :param _db: A connection to the database.
        :param bots: A list of BotModel objects.
        """
        self._db = _db
        self.bots = bots

    @classmethod
    def from_directory(cls, directory, consider_only=None):
        """Load database and configuration from a directory on disk.

        The database is kept in `botfriend.sqlite` and bots are found
        in subdirectories.
        """
        log = logging.getLogger("Loading configuration from %s" % directory)
        database_path = os.path.join(directory, 'botfriend.sqlite')
        _db = production_session(database_path)
        botmodels = []
        seen_names = set()
        package_init = os.path.join(directory, '__init__.py')
        if not os.path.exists(package_init):
            log.warn(
                "%s does not exist; creating it so I can treat %s as a package.",
                package_init, directory
            )
            open(package_init, 'w').close()
        if not directory in sys.path:
            logging.info("Adding %s to sys.path" % directory)
            sys.path.append(directory)
        for f in os.listdir(directory):
            bot_directory = os.path.join(directory, f)
            if os.path.isdir(bot_directory):
                # It's a directory; does it contain a bot?
                can_load = True
                for expect in ('__init__.py', 'bot.yaml'):
                    path = os.path.join(bot_directory, expect) 
                    if not os.path.exists(path):
                        logging.warn(
                            "Not loading %s: missing %s",
                            f, expect
                        )
                        can_load = False
                        break
                if can_load:
                    botmodel = BotModel.from_directory(_db, bot_directory)
                    if consider_only and (
                            botmodel.name not in consider_only
                            and f not in consider_only
                    ):
                        continue
                    if botmodel.name in seen_names:
                        raise Exception(
                            "Two different bots are configured with the same name. (%s)" % botmodel.name
                        )
                    seen_names.add(botmodel.name)
                    botmodels.append(botmodel)
                    
        return Configuration(_db, botmodels)
                
