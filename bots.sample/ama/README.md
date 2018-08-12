I Am A Bot. AMA!

https://twitter.com/iamabotama
https://botsin.space/@IAmABotAMA

This complex TextGeneratorBot demonstrates some advanced features of
botfriend:

* State management. Raw data is periodically gathered from Twitter and
   stored in Bot.state.  This happens in IAMABot.update_state, which
   is called every eight hours (state_update_frequency: 480 in
   bot.yaml).

* Use of publisher credentials (Twitter) to maintain state.

* The bot examines its recent posts using BotModel.recent_posts(), in
  an attempt not only to avoid exact duplicates but to avoid repeating
  key words too frequently.

Since this bot gets its entire dataset from Twitter, you'll need to
give it Twitter credentials to run it.
