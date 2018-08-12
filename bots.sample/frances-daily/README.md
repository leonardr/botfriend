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

Use the scheduled-load script to load the script.

$ ./scheduled-load --config=sample-bots --bot=frances-daily --file=sample-bots/frances-daily/script.ndjson

Once that's done, use the post script to post items:

$ ./post --config=sample-bots --bot=frances-daily

The output will be published to sample-bots/frances-daily/Frances Daily.txt.

Note that this bot will never publish a post until its scheduled time
has passed.
