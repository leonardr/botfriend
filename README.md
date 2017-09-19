# botfriend

Botfriend is a Python framework for managing a lot of creative bots that
post to a lot of different places. Its primary features:

* Minimal Python coding -- just write the interesting part of your bot.
* Simple YAML-based configuration.
* Easy post scheduling.
* Can post to Twitter, Mastodon, and/or Tumblr.
* Built-in access to [olipy](https://github.com/leonardr/olipy) for
   Queneau assembly, Markov chains, and other artistic randomness tools.
* Built-in access to common data sets through [corpora](https://github.com/dariusk/corpora/).

# Setup

After cloning this repository, run these commands to set up 

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
git submodule init
cd olipy
git submodule init
```

# Getting started

All the botfriend scripts take a `--config` argument that points to
your botfriend directory. The database will be stored in this
directory as `botfriend.sqlite`. Each individual bot is kept in a
subdirectory of your botfriend directory.

To get started, try using the `sample-bots` directory, which contains
more than ten sample bots.

You can see what the bots are up to with the `dashboard` script. 

```
./dashboard --config=sample-bots
```

(All the example commands in this document assume you have run `source
env/bin/activate` first to get into the botfriend virtual
environment.)

The `dashboard` script will tell you the last time each bot posted,
the next time it's going to post, what it last posted, and (if known)
the next thing it's going to post.

To tell the bots to actaully post something, run the `post` script:

```
./post --config=sample-bots
```

At this point, some of the sample bots will raise a `NothingToPost`
exception. [Roy's Postcards](https://github.com/leonardr/botfriend/tree/master/sample-bots/postcards) and [Deathbot 3000]https://github.com/leonardr/botfriend/tree/master/sample-bots/roller-derby) are example. These bots
can only post from a backlog or from prescheduled posts. If nothing is
scheduled, they have nothing to post.

Other bots, like [Best of
RHP](https://github.com/leonardr/botfriend/tree/master/sample-bots/best-of-rhp)
and [Ingsoc Party
Slogans](https://github.com/leonardr/botfriend/tree/master/sample-bots/ingsoc-slogans),
will raise `TweepError` at this point. These bots need working Twitter
credentials to function, and none of the sample bots are supplied with
valid Twitter credentials.

But most of the bots in `sample-bots` will work fine. They will create
and publish one or more posts. These posts won't be published to
Twitter, since the sample bots don't have Twitter
credentials. Instead, the posts will be published to files in the bot
directories.

For example, [A Dull
Bot](https://github.com/leonardr/botfriend/tree/master/sample-bots/a-dull-bot) will write its posts to
`sample-bots/a-dull-bot/a-dull-bot.txt`.

[Crowd Board
Games](https://github.com/leonardr/botfriend/tree/master/sample-bots/crowd-board-games)
will convert an entire RSS feed into a series of posts, and write them
all to `sample-bots/crowd-board-games/crowd-board-games.txt`.

[Anniversary
Materials](https://github.com/leonardr/botfriend/tree/master/sample-bots/anniversary)
can get extra data from Twitter if it has Twitter credentials, but it
won't crash or give up if those credentials are missing -- it will
come up with gift ideas using the built-in datasets, and write its
posts to `sample-bots/anniversary/anniversary.txt`.

If you run `./dashboard --config=sample-bots` again, you'll see that
the results of running `post` have been archived in the database at
`sample-bots/botfriend.sqlite`.

The second time you run `./post --config=sample-bots`, you'll see a
lot less action. The bots that crashed the first time will crash the
second time, but most of the bots will be silent. This is because they
just posted something. Every bot has some kind of scheduling rules
that limit how often it posts. Generally you don't want bots to post
more than once an hour.

If you want to force a specific bot to post, despite its schedule, you
can use the `--force` option, like this:

```
./post --config=sample-bots --bot=anniversary --force
```

# Bot anatomy

So, you've got about ten examples to look at. Each bot directory
contains two special files: one for configuration and one for code.

# `bot.yaml`

This is a YAML file which contains all the information necessary to
configure your bot. You can put anything you want in here, but you
need to supply three pieces of information:

* The name of your bot
* How often the bot should post things
* The specific services to post to, and API credentials that can be used
  on those services.

Configuration options are covered in more detail below, but here's a
simple example: the `bot.yaml` for [Serial
Entrepreneur](https://github.com/leonardr/botfriend/tree/master/sample-bots/serial-entrepreneur).

```
name: "Serial Entrepreneur"
schedule:
    mean: 150
    stdev: 30
publish:
    file:
      filename: "Serial Entrepreneur.txt"
```

This is saying:

* The name of the bot is "Serial Entrepreneur".

* The bot should publish something once every two-and-a-half hours
  (150 minutes). But rather than publishing every 150 minutes on the
  dot, the scheduling should vary randomly, with a standard deviation
  of thirty minutes. That is, the posts will frequently be as little
  as 120 minutes, or as much as 180 minutes apart.

* When it's time for the bot to publish something, the 'something'
  should be written to the file `Serial Entrpreneur.txt`.

# `__init__.py`

This is where the bot's code lives. There's only one rule here: you
have to define a class called `Bot`. The `botfriend` scripts are going
to load that class, instantiate it, and use it to make that bot's
contribution to whatever the script is supposed to do. The bot may be
asked to post something, list previous posts, or whatever.

If you want to write a lot of bot code yourself, you can subclass
`BasicBot`.

```
from bot import BasicBot
class Bot(BasicBot):
      ...
```

But for most common types of bot, there's a more specific class you
can subclass, and eliminate most of the work.

## Bots that generate posts on demand

The simplest type of bot generates a totally new string every time
it's invoked. There's no need to schedule posts in advance or create a
backlog.

To create this kind of bot, subclass
[`TextGeneratorBot`](https://github.com/leonardr/botfriend/blob/master/bot.py)
and implement the `generate_text()` method to return the string you
want to post.

Several examples of `TextGeneratorBot` are included with botfriend,
the simplest being [A Dull
Bot](https://github.com/leonardr/botfriend/tree/master/sample-bots/a-dull-bot).
Here's all of the code for A Dull Bot:

```
from olipy.typewriter import Typewriter
from olipy.integration import pad
from bot import TextGeneratorBot

class TypewriterBot(TextGeneratorBot):

    def generate_text(self):
        typewriter = Typewriter()
        text = typewriter.type("All work and no play makes Jack a dull boy.")
        return pad(text)
        
Bot = TypewriterBot
```

[Euphemism
Bot](https://github.com/leonardr/botfriend/tree/master/sample-bots/euphemism)
and [Serial
Entrepreneur](https://github.com/leonardr/botfriend/tree/master/sample-bots/serial-entrepreneur)
have more complex generative logic, but they're still very simple
`TextGeneratorBot`s. They don't keep track of any data outside of
their core datasets.

[I Am A
Bot. AMA!](https://github.com/leonardr/botfriend/tree/master/sample-bots/ama)
is a more complicated `TextGeneratorBot` that stores state between
invocations to minimize load on the Twitter API.

## Bots that post from a predefined list

Instead of creating a new post every time it's time for the bot to
act, you can list out all the things the bot should post ahead of
time, and have the bot post off the list.

There are two ways to do this. If you're scripting a bot and you need
posts to be published at specific dates and times, you can schedule
posts. Most of the time, though, you need posts to be published at
rough intervals but not at specific times. In that case, it's easier
to create a backlog.

### Bots that post from a backlog

When you have a large number of posts and the exact timing isn't
particularly important, the best thing to do is to dump all those
posts into your bot's backlog. Every time your bot is asked to post
something, it will pick the top item off the backlog and send it to be
published.

[Boat Name
Bot](https://github.com/leonardr/botfriend/tree/master/sample-bots/boat-names)
is a bot that has no custom code whatsoever. It does nothing but post
strings from its backlog. The code for Boat Name Bot is just a
placeholder:

```
from bot import Bot
```

The real action is in the `backload-load` script, which loads items
into the backlog from a text file. Boat Name Bot comes with a [sample backlog
of boat names](https://github.com/leonardr/botfriend/blob/master/sample-bots/boat-names/backlog.txt), which you can load with a command like this:

```
./backlog-load --config=sample-bots --bot=boat-names --file=sample-bots/boat-names/input.txt
```

Once you've loaded a backlog, the `./post` script will start posting
items off the backlog, gradually, one at a time. With a backlog bot,
there's almost no risk of something going wrong while the bot is in
operation, because you've do all the work ahead of time.

[Death Bot
3000](https://github.com/leonardr/botfriend/tree/master/sample-bots/roller-derby)
is a backlog bot that is a little more complicated. Instead of keeping
its backlog in a text file, it expects its backlog in the form of
[JSON
lists](https://github.com/leonardr/botfriend/blob/master/sample-bots/roller-derby/backlog.ndjson).
To convert from a JSON list to a string, Death Bot 3000 subclasses the
`object_to_post` method.

### Bots that act out a script

The default assumption of botfriend is that a bot should post at a
certain interval, but that the exact times aren't important. Most of
the time you _want_ a little variation in the posting time, so that
your bot doesn't post at "bot o'clock", the same time once an
hour. But sometimes the exact timing _is_ important.

If it's important that your bost posts at specific times, you can have
your bot schedule those posts in advance.

[Frances
Daily](https://github.com/leonardr/botfriend/tree/master/sample-bots/frances-daily)
schedules posts for specific dates, exactly thirty years after the
journal items were originally written. On some days, there is no post
at all. So there's no simple rule like "every day, publish the next
post." Each post needs to have a 

You can create schedule posts without writing any special code at
all. Frances Daily doesn't have any special code -- it uses [a simple
JSON script
format](https://github.com/leonardr/botfriend/blob/master/sample-bots/frances-daily/script.ndjson)
to explain what should be published when.

To load scheduled posts, use the `scheduled-load` script. Here's an
example that  loads the script for Frances Daily:

```
./scheduled-load --config=sample-bots --bot=frances-daily --file=sample-bots/frances-daily/script.ndjson
```

Once you load the scheduled posts, the `./post` script will start
posting them. Note that it won't post items that are more than a few
days old.

### Bots can post images

Bots can post images as well as text. [Roy's
Postcards](https://github.com/leonardr/botfriend/tree/master/sample-bots/postcards)
is an example of a bot that loads a combination of images and text
into its backlog. In this case the images are loaded off disk when it's time to
post them -- only the filenames are stored in the backlog.

# Tracking bot-specific state

[I Am A
Bot. AMA!](https://github.com/leonardr/botfriend/tree/master/sample-bots/ama)
gets its data by using the Twitter API to run searches on strings like
"i am a" and "i am an". These searches take a long time and can cause
Twitter to rate-limit the bot. Rather than go through this process
every single time the bot wants to post, the `IAmABot` class
implements the `update_state` method. This method performs the
searches and returns the raw data in a JSON string that's stored in the
database.

When it's time for the bot to post something, the current value of the
bot's state is accessible through the property `self.model.state`. 

You can store whatever you want in the bot's state. Anything that can
be cached and is time-consuming to calculate is a good
choice. [Anniversary
Materials](https://github.com/leonardr/botfriend/tree/master/sample-bots/anniversary)
is another example--it also uses the Twitter search API to gather raw
data from Twitter.

# Configuration

Let's take another look at [Serial
Entrepreneur's bot.yaml](https://github.com/leonardr/botfriend/tree/master/sample-bots/serial-entrepreneur/bot.yaml):

```
name: "Serial Entrepreneur"
schedule:
    mean: 150
    stdev: 30
publish:
    file:
      filename: "Serial Entrepreneur.txt"
```

`name` should be self-explanatory -- it's the human-readable name of
the bot.

## `schedule`

The `schedule` configuration option controls how often your bot should
post. There are basically three strategies.

1. Set `schedule` to a number of minutes. Your bot will post at exact
intervals, with that number of minutes between posts.
2. Give `schedule` a `mean` number of minutes. Your bot will post at
randomly determined intervals, with _approximately_ that number of
minutes between posts.
3. To fine-tune the randomness, you can specify a `stdev` to go along
with the mean. This sets the standard deviation used when calculating
when the next post should be. Set it to a low number, and posts will
nearly `mean` minutes apart. Set it to a high number, and the posting
schedule will vary widely.

You can omit `schedule` if your bot schedules all of its posts ahead
of time (like [Frances
Daily](https://github.com/leonardr/botfriend/tree/master/sample-bots/frances-daily)
does).

`schedule`, and `publish` are only the most common
configuration options.  [Best of
RHP](https://github.com/leonardr/botfriend/tree/master/sample-bots/best-of-rhp),
a subclass of `RetweetBot`, has a special configuration setting called
`retweet-user`, which controls the Twitter account that the bot
retweets.

### `state_update_schedule`

There's a related option, `state_update_schedule`, which you only need
to set if your bot keeps internal state, like [I Am A
Bot. AMA!](https://github.com/leonardr/botfriend/tree/master/sample-bots/ama)
does. This option works the same way as `schedule`, but instead of
controlling how often the bot should post, it controls how often your
`update_state()` method is called.

## Publication

Underneath the `publish` configuration setting, list the various
techniques you want your bot to use when publishing its posts to the
Internet. Almost all of my bots post to both Twitter and Mastodon; one
posts to Tumblr as well.

Sometimes you'll need to communicate with an API for more than just
posting. You can always access a publisher from inside a `Bot` as
`self.publishers`, and the raw API will always be available as
`Publisher.api`.

See the `IAmABot` constructor for an example -- it needs a Twitter API
client to run a search, so it looks through `self.publishers` until it
finds the Twitter publisher, and grabs its `.api`, storing it for
later.

## Publish to a file

This is the simplest publication technique, and it's really only good
for testing and keeping a log. The `file` publisher takes one
configuration setting: `filename`, the name of the file to write to.

```
publish:
    file:
        filename: "anniversary.txt"
```

## Twitter

To post to 

## Mastodon

## Tumblr


## Defaults

If you put a file called `default.yaml` in your `botfriend` directory
(next to `botfriend.sqlite`), all of your bots will inherit the values
in that file.

Almost all my bots use the same Mastodon and Twitter client keys (but
different application keys). I keep the client keys in `default.yaml`
so I don't have to repeat them in every single `bot.yaml` file. My
`default.yaml` looks like this:

```
publish:
  mastodon: {api_base_url: 'https://botsin.space/', client_id: a, client_secret: b}
  twitter: {consumer_key: c, consumer_secret: d}
```

This way, inside a given `bot.yaml` file, I only have to fill in the
information that's not specified in `default.yaml`:

```
name: My Bot
publish:
 mastodon:
  access_token: efg
 twitter:
  access_token: hij
  access_token_secret: klm
schedule:
 mean: 120
```

# Posting

To set up botfriend, use a cron job to schedule the `post` script to
run every few minutes. If any bots need to post something, they'll
post it. Any bots that don't need to post anything right now will be
quiet.

Here's what my cron script looks like:

```
#!/bin/bash
export ROOT=/home/leonardr/scripts/botfriend
source $ROOT/env/bin/activate
$ROOT/post --config=$ROOT/bots
```

Here's how I use a cron job to run it once a minute:

```
* * * * * /home/leonardr/scripts/botfriend/cron >> /home/leonardr/scripts/botfriend_err
```
