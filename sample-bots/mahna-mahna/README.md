Mahna Mahna
http://twitter.com/mahna____mahna
https://botsin.space/@MahnaMahna

This bot illustrates some advanced features of BotFriend:

* The use of Bot.schedule_posts() to schedule posts in advance.
* The use of code, rather than a script, to schedule posts.

This bot will not post anything until you tell it to schedule posts:

$ ./scheduled-load --config=bots --bot=mahna-mahna

Even then, it may refuse to schedule posts. For example, it will not
schedule posts during the weekend.

Once the posts are scheduled, you can post one (assuming its scheduled
time has passed) with the 'post' script.

$ ./post --config=bots --bot=mahna=mahna
