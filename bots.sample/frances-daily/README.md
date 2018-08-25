Frances Daily
https://twitter.com/FrancesDaily

This is a scripted bot that posts at exactly the same time on specific
days over a long period of time. There is no special code--everything
is contained in the script file.

The data is the official Frances Daily data, but with the scheduled
times modified to post between 2017 and 2023, rather than between 2012
and 2018.

This bot demonstrates some advanced features of botfriend:

* You can use a simple NDJSON script to have posts with specific
  content published at specific times, rather than semi-randomly.

* To avoid overloading the publishing mechanism, posts scheduled for
  the past will not be imported.

Use botfriend.backlog.load to load the script.

$ botfriend.backlog.load -frances-daily --file=bots.sample/frances-daily/script.ndjson

Once that's done, use botfriend.post to post items:

```
$ botfriend.post frances-daily
# Backlog load script | Appended 1434 items to backlog.
# Backlog load script | Backlog size now 1434 items
```

The output will be published to sample-bots/frances-daily/Frances Daily.txt.

Note that this bot will never publish a post until its scheduled time
has passed. It will also not publish a post that should have been
published a long time ago, but wasn't.
