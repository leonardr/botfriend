import importlib
import os
import sys
from nose.tools import set_trace
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import (
    relationship,
)
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def get_one_or_create(db, model, create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    """Get a single model object. If it doesn't exist, create it."""
    one = get_one(db, model, **kwargs)
    if one:
        return one, False
    else:
        __transaction = db.begin_nested()
        try:
            # These kwargs are supported by get_one() but not by create().
            get_one_keys = ['on_multiple', 'constraint']
            for key in get_one_keys:
                if key in kwargs:
                    del kwargs[key]
            obj = create(db, model, create_method, create_method_kwargs, **kwargs)
            __transaction.commit()
            return obj
        except IntegrityError, e:
            logging.info(
                "INTEGRITY ERROR on %r %r, %r: %r", model, create_method_kwargs, 
                kwargs, e)
            __transaction.rollback()
            return db.query(model).filter_by(**kwargs).one(), False


def production_session(filename):
    """Get a database connection to the SQLite database at `filename`."""
    engine = create_engine('sqlite:///%s' % filename, echo=True)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    session = Session(connection)
    return session


class Bot(Base):
    __tablename__ = 'bots'
    id = Column(Integer, primary_key=True)

    # The name of the directory containing the bot's configuration and
    # code.
    name = Column(String)

    # If this is set, the bot will not post anything until this time.
    next_post_time = Column(DateTime)

    posts = relationship('Post', backref='bot')
    
    @property
    def log(self):
        return logging.getLogger("Bot %s" % self.name)

    @classmethod
    def from_directory(self, _db, directory):
        """Load bot code from `directory`, and find or create the
        corresponding Bot object.

        Note that the parent of `directory` must be in sys.path
        """
        path, module = os.path.split(directory)
        bot_module = importlib.import_module(module)
        bot_class = getattr(bot_module, "Bot", None)
        if not bot_class:
            raise Exception(
                "Loaded module %s but could not find a class called Bot inside." % bot_module
            )

        set_trace()
    
    def post(self):
        now = datetime.datetime.utcnow()
        if self.next_post_time and now < self.next_post_time:
            self.log.info("Not posting until %s" % self.next_post_time)

        
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    bot_id = ForeignKey('bots.id', index=True, nullable=False)

    # The time the post was, or is supposed to be, delivered.
    date = Column(DateTime)

    # The original content of the post. This may need to be cut down
    # for specific delivery mechanisms, but that's okay -- we know how
    # to do that automatically.
    content = Column(String)
    
    deliveries = relationship('deliveries', backref='post')
    attachments = relationship('attachments', backref='post')
    

class Delivery(Base):
    """A record that a post was delivered to a specific service,
    or at least that the attempt was made.
    """
    __tablename__ = 'deliveries'
    id = Column(Integer, primary_key=True)
    post_id = ForeignKey('posts.id', index=True, nullable=False)

    # The service we delivered this post to.
    service = Column(String)

    # The service uses this ID to refer to the post.
    # (e.g. Twitter assigns the post an ID when it becomes a tweet).
    external_id = Column(String, index=True)
    
    # The first time we tried to deliver this post.
    first_attempt = Column(DateTime)

    # The most recent time we tried to deliver this post.
    most_recent_attempt = Column(DateTime)

    # The reason, if any, we couldn't deliver this post.
    error = Column(String)
    

class Attachment(Base):
    """A file (usually a binary image) associated with a post."""
    
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True)
    post_id = ForeignKey('posts.id', index=True, nullable=False)

    # The filename is relative to the bot directory. For some bots,
    # images are placed in the appropriate spot ahead of time.  For
    # others, images are generated as posting time and archived in
    # these paths.
    filename = Column(String, index=True)
