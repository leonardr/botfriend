import datetime
import importlib
import logging
import os
import sys
import yaml
from nose.tools import set_trace
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.exc import (
    IntegrityError
)
from sqlalchemy.orm import (
    backref,
    relationship,
)
from sqlalchemy.orm.exc import (
    NoResultFound,
    MultipleResultsFound,
)
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base


TIME_FORMAT = "%Y-%m-%d %H:%M"

def _now():
    """The current time.

    I've moved this into a function so I can test out whether
    local time or UTC is better for this purpose.
    """
    return datetime.datetime.now()

Base = declarative_base()

def create(db, model, create_method='',
           create_method_kwargs=None,
           **kwargs):
    """Create a single model object."""
    kwargs.update(create_method_kwargs or {})
    created = getattr(model, create_method, model)(**kwargs)
    db.add(created)
    db.flush()
    return created, True

def get_one(db, model, on_multiple='error', **kwargs):
    """Gets an object from the database based on its attributes.

    :return: object or None
    """
    q = db.query(model).filter_by(**kwargs)
    try:
        return q.one()
    except MultipleResultsFound, e:
        if on_multiple == 'error':
            raise e
        elif on_multiple == 'interchangeable':
            # These records are interchangeable so we can use
            # whichever one we want.
            #
            # This may be a sign of a problem somewhere else. A
            # database-level constraint might be useful.
            q = q.limit(1)
            return q.one()
    except NoResultFound:
        return None


def get_one_or_create(db, model, create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    """Get a single model object. If it doesn't exist, create it."""
    one = get_one(db, model, **kwargs)
    if one:
        return one, False
    else:
        try:
            # These kwargs are supported by get_one() but not by create().
            get_one_keys = ['on_multiple', 'constraint']
            for key in get_one_keys:
                if key in kwargs:
                    del kwargs[key]
            obj = create(db, model, create_method, create_method_kwargs, **kwargs)
            return obj
        except IntegrityError, e:
            logging.info(
                "INTEGRITY ERROR on %r %r, %r: %r", model, create_method_kwargs, 
                kwargs, e)
            return db.query(model).filter_by(**kwargs).one(), False


def production_session(filename):
    """Get a database connection to the SQLite database at `filename`."""
    engine = create_engine('sqlite:///%s' % filename, echo=False)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    session = Session(connection)
    return session


class BotModel(Base):
    __tablename__ = 'bots'
    id = Column(Integer, primary_key=True)

    # The name of the directory containing the bot's configuration and
    # code.
    name = Column(String)

    # If this is set, the bot will not post anything until this time.
    next_post_time = Column(DateTime)

    # The bot's implementation may store anything it wants in this field
    # to keep track of state between posts.
    state = Column(String)
    
    posts = relationship('Post', backref='bot')
    
    @property
    def log(self):
        return logging.getLogger(self.name)
   
    @classmethod
    def from_directory(self, _db, directory):
        """Load bot code from `directory`, and find or create the
        corresponding BotModel object.

        Note that the parent of `directory` must be in sys.path

        :return: A Bot object with a reference to the appropriate
        BotModel.
        """
        path, module = os.path.split(directory)
        bot_module = importlib.import_module(module)
        bot_class = getattr(bot_module, "Bot", None)
        if not bot_class:
            raise Exception(
                "Loaded module %s but could not find a class called Bot inside." % bot_module
            )
        bot_config_file = os.path.join(directory, "bot.yaml")
        if not os.path.exists(bot_config_file):
            raise Exception(
                "Bot config file %s not found." % bot_config_file
            )
        config = yaml.load(open(bot_config_file))
        name = config.get('name')
        if not name:
            raise Exception(
                "Bot config file (%s) does not define a value for 'name'!" %
                bot_config
            )
        bot_model, is_new = get_one_or_create(_db, BotModel, name=name)
        bot_implementation = bot_class(bot_model, directory, config)
        bot_model.implementation = bot_implementation
        return bot_model

    @property
    def next_unpublished_posts(self):
        """Find the already existing Post (or Posts) next in line to be
        published.

        :return: A list of Posts.
        
        Only Posts with no Publications are considered.

        If there are any Posts with `publish_at` before the current time,
        all such Posts are returned.

        If not, the oldest Post with `publish_at` not set is chosen.

        If there are no Posts with `publish_at` not set, an empty list
        is returned.
        """
        _db = Session.object_session(self)
        now = _now()
        base_query = _db.query(Post).filter(
            Post.bot==self).outerjoin(
                Post.publications).filter(
                    Publication.id==None)
        past_due = base_query.filter(Post.publish_at <= now).order_by(
            Post.publish_at.asc()).all()
        if past_due:
            return past_due
        
        next_in_line = base_query.filter(Post.publish_at == None).order_by(
            Post.created.asc()).limit(1).all()
        return next_in_line
    
    def next_posts(self):
        """Find or create one or more Posts that are ready to be published.
        Don't publish it.
        
        :return: A list of Posts, possibly empty.
        """
        now = _now()
        unpublished = self.next_unpublished_posts
        if unpublished:
            return unpublished

        # Maybe we should create a new post.
        if self.next_post_time and now < self.next_post_time:
            # Nope.
            self.log.info("Not posting until %s" % (
                self.next_post_time.strftime(TIME_FORMAT)
            ))
            return []
        
        new_posts = self.new_posts()
        
        # Don't automatically use the new posts. It might not be time to publish
        # all of them. This will find the publishable ones.
        return self.next_unpublished_posts

    def new_posts(self):
        """Create one or more brand new posts.

        This will call Bot.schedule_next_post to set the next time more
        posts should be scheduled.
        
        :return: The new Posts, in a (possibly empty) list.
        """
        new_posts = self.implementation.new_post()
        if not new_posts:
            new_posts = []
        elif isinstance(new_posts, basestring):
            new_posts = [Post.from_content(self, new_posts)]
        elif isinstance(new_posts, Post):
            new_posts = [new_posts]
        self.next_post_time = self.implementation.schedule_next_post(
            new_posts
        )
        return new_posts

        
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    bot_id = Column(
        Integer, ForeignKey('bots.id'), index=True, nullable=False
    )

    # The time the post was created.
    created = Column(DateTime)
    
    # The time the post was/is supposed to be published.
    publish_at = Column(DateTime)

    # The original content of the post. This may need to be cut down
    # for specific publication mechanisms, but that's okay -- we know how
    # to do that automatically.
    content = Column(String)

    # A Post may be a reply to another botfriend post.
    reply_to_id = Column(
        Integer, ForeignKey('posts.id'), index=True, nullable=True
    )

    # Or it might be a reply to another post on some other service.
    reply_to_foreign_id = Column(String, index=True)
    
    replies = relationship(
        "Post", backref=backref("reply_to", remote_side=[id])
    )
    
    publications = relationship('Publication', backref='post')
    attachments = relationship('Attachment', backref='post')

    @classmethod
    def from_content(cls, bot, content, publish_at=None):
        """Turn a string of content into a Post."""
        _db = Session.object_session(bot)
        post, is_new = create(_db, Post, bot=bot)
        post.content = content
        now = _now()
        post.created = now
        post.publish_at = publish_at or now
        return post

    @property
    def content_snippet(self):
        "A small string of content suitable for logging."
        if self.content:
            return self.content[:20]
        else:
            return "[no textual content]"
    
    def publish(self):
        """Publish this Post to every service registered with the bot.

        :return: A list of Publications.
        """
        now = _now()
        if self.publish_at and self.publish_at >= now:
            logging.warn(
                "Not publishing %s until %s", self.content,
                self.publish_at.strftime(self.TIME_FORMAT)
            )
            return []
        return self.bot.implementation.publish(self)
        

class Publication(Base):
    """A record that a post was published to a specific service,
    or at least that the attempt was made.
    """
    __tablename__ = 'publications'
    id = Column(Integer, primary_key=True)
    post_id = Column(
        Integer, ForeignKey('posts.id'), index=True, nullable=False
    )

    # The service we published this post to.
    service = Column(String)

    # The service uses this ID to refer to the post.
    # (e.g. Twitter assigns the post an ID when it becomes a tweet).
    external_id = Column(String, index=True)
    
    # The first time we tried to publish this post.
    first_attempt = Column(DateTime)

    # The most recent time we tried to publish this post.
    most_recent_attempt = Column(DateTime)

    # The reason, if any, we couldn't publish this post. If this
    # is None, it is assumed the post was successfully published.
    error = Column(String)

    def display(self):
        if self.error:
            msg = self.error
            if self.most_recent_attempt != self.first_attempt:
                msg += " (since %s)" % self.first_attempt
        else:
            msg = "Published %s" % self.most_recent_attempt.strftime(TIME_FORMAT)
        return "%s | %s | %s " % (self.service, msg, self.post.content_snippet)
        
    def report_attempt(self, error=None):
        "Report a (possibly successful) attempt to publish this post."
        now = _now()
        if not self.first_attempt:
            self.first_attempt = now
        self.most_recent_attempt = now
        self.error = error

    def report_success(self):
        self.report_attempt(error=None)
        
    def report_failure(self, error="Unknown error."):
        if isinstance(error, Exception):
            error = str(error.message)
        self.report_attempt(error)

class Attachment(Base):
    """A file (usually a binary image) associated with a post."""
    
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True)
    post_id = Column(
        Integer, ForeignKey('posts.id'), index=True, nullable=False
    )

    # The filename is relative to the bot directory. For some bots,
    # images are placed in the appropriate spot ahead of time.  For
    # others, images are generated as posting time and archived in
    # these paths.
    filename = Column(String, index=True)
