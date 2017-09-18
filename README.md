# botfriend

Botfriend is a Python framework for managing a lot of creative bots that
post to a lot of different places.

* Simple YAML-based configuration
* Easy post scheduling
* Built-in access to [olipy](https://github.com/leonardr/olipy) and
  [corpora](https://github.com/dariusk/corpora/).
* Post to Twitter, Mastodon, and/or Tumblr.

# Bots that generate posts on demand

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

[I Am A
Bot. AMA!](https://github.com/leonardr/botfriend/tree/master/sample-bots/ama)
is a more complicated `TextGeneratorBot` that stores state between
invocations to minimize load on the Twitter API.

# Creating posts in advance

Instead of creating a new post every time it's time for the bot to
act, you can list out all the things the bot should post, and have the
bot post of the list.

There are two ways to do this. If you're scripting a bot and you need
posts to be published at specific dates and times, you can schedule
posts. Most of the time, though, you need posts to be published at
rough intervals but not at specific times. In that case, it's easier
to create a backlog.

## Creating a backlog

When you have a large number of posts and the exact timing isn't
particularly important, the best thing to do is to dump all those
posts into your bot's backlog. Every time your bot is asked to post
something, it will pick the top item off the backlog and send it to be
published.

[Boat Name
Bot](https://github.com/leonardr/botfriend/tree/master/sample-bots/boat-names)
is a bot that has no custom code whatsoever. It does nothing but post
strings from its backlog.

Instead of strings, [Death Bot
3000](https://github.com/leonardr/botfriend/tree/master/sample-bots/roller-derby)
keeps a backlog full of JSON objects. It has custom code for
converting the JSON object to a string for posting. This lets you go
into the code over time and tweak how you want the data to be
formatted. You don't have to commit to the exact strings you want to
post when you build the backlog.

To load a backlog, use the `backload-load` script. Here's how you
could use it to load a backlog of over 9,000 items into the Boat Name
Bot script.

```
source env/bin/activate
./backlog-load --config=sample-bots --bot=boat-names < sample-bots/boat-names/input.txt
```

## Scheduling posts for specific times

The default assumption of botfriend is that a bot should post at a
certain interval, but that the exact times aren't important. But
sometimes the exact time _is_ important.

If it's important that your bost posts at specific times, you can have
your bot schedule those posts instead of creating a backlog.

[Frances
Daily](https://github.com/leonardr/botfriend/tree/master/sample-bots/frances-daily)
schedules posts for specific dates, exactly thirty years after the
items were originally written. On some days, there is no post at
all. So there's no simple rule like "every day, publish the next
post."

You can create schedule posts without writing any special code at
all. Frances Daily doesn't have any special code -- it uses a simple
JSON script format to explain when the posts should be published.

To load scheduled posts, use the `scheduled-load` script. Here's an
example that  loads the script for Frances Daily:

```
source env/bin/activate
./scheduled-load --config=sample-bots --bot=frances-dail --file=sample-bots/frances-daily/script.ndjson
```


# Tracking bot-specific state

# Publication

## Twitter

## Mastodon

## Tumblr

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
