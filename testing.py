from datetime import datetime
from sqlalchemy.orm.session import Session
from model import (
    create,
    get_one_or_create,
    engine,
    Base,
    BotModel,
    Post,
    Publication,
)


class DatabaseTest(object):

    # These variables are set appropriately by package_setup.
    engine = None
    connection = None

    def setup(self):
        # Create a new connection to the database.
        self._db = Session(self.connection)
        self.transaction = self.connection.begin_nested()

        # Start with a high number so it won't interfere with tests that
        # search for a small number.
        self.counter = 2000

        self.time_counter = datetime(2014, 1, 1)
        
    def teardown(self):
        # Close the session.
        self._db.close()

        # Roll back all database changes that happened during this
        # test, whether in the session that was just closed or some
        # other session.
        self.transaction.rollback()

    @property
    def _id(self):
        self.counter += 1
        return self.counter

    @property
    def _str(self):
        return unicode(self._id)

    @property
    def _time(self):
        v = self.time_counter 
        self.time_counter = self.time_counter + timedelta(days=1)
        return v

    def _botmodel(self, name=None):
        name = name or self._str
        bot, is_new = get_one_or_create(
            self._db, BotModel, name=name
        )
        return bot

    def _post(self, botmodel=None, content=None, publish_at=None,
              reuse_existing=True, published=False):
        botmodel = botmodel or self._botmodel()
        content = content or self._str
        post, is_new = Post.from_content(
            bot=botmodel, content=content, publish_at=publish_at,
            reuse_existing=reuse_existing
        )
        if published:
            self._publication(botmodel, post)
        return post

    def _publication(self, botmodel=None, post=None, service=None,
                     success=True):
        if post:
            botmodel = post.bot
        elif not botmodel:
            botmodel = self._botmodel()
        if not post:
            post = self._post(botmodel)
        service = service or self._str
        publication, is_new = get_one_or_create(
            self._db, Publication, post=post, service=service
        )
        if success:
            publication.report_success()
        return publication

    
def package_setup():
    """Initialize an in-memory SQLite database to be used by
    the test suite.
    """
    DatabaseTest.engine, DatabaseTest.connection = engine(":memory:")

