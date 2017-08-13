Roy's Postcards

 https://twitter.com/RoyPostcards
 https://botsin.space/@royspostcards

This is the official code, but only three sample postcards are
included, plus the metadata for a fourth card that is not present.

This example demonstrates some advanced features of botfriend:

* You can load posts with attachments into the backlog. If a post
  mentions an attachment that can't be found, that post will be skipped
  and not loaded into the backlog.

* You can publish dramatically different content to different
  publications. The higher Mastodon character limit allows the
  postcard inscription to be included in the post, versus the Twitter
  publication, which only includes a link and tags.

* The JSON document that is kept in the backlog is stored as
  Post.state once the Post object is created. You can access this in
  Bot.post_to_publisher() to customize what gets sent to which
  publisher.

* A bot may disable off the normal checks that prevent duplicate posts
  by setting "duplicate_filter: false" in bot.yaml. Since Roy's
  Postcards runs in a loop, with the backlog being refilled whenever
  it empties, it's expected that identical posts will appear about
  three years apart.
