from sqlalchemy import (
    create_engine,
    ForeignKey,
)
from sqlalchemy.orm import (
    relationship,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Datetime,
)

Base = declarative_base()

def production_session():
    engine = create_engine('sqlite:///:memory:', echo=True)
    
class Bot(Base):
    __tablename__ = 'bots'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    next_post_time = Column(Datetime)

    @property
    def log(self):
        return logging.getLogger("Bot %s" % self.name)

    @property
    def config(self):
        if not hasattr(self, '_config'):
            self._load_config()
        return self._config

    def _load_config(self):
        """Load YAML config from the `{name}/config.yaml` file.

        Also imports the appropriate module.
        """
        
    def post(self):
        now = datetime.datetime.utcnow()
        if self.next_post_time and now < self.next_post_time:
            self.log.info("Not posting until %s" % self.next_post_time)

        
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    bot_id = ForeignKey('bots.id')

    # The time the post was, or is supposed to be, delivered.
    date = Column(Datetime)
    

class Delivery(Base):
    """A record that a post was delivered to a specific service."""
