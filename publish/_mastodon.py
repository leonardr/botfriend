from nose.tools import set_trace
from mastodon import Mastodon
from bot import Publisher

class MastodonPublisher(Publisher):
    def __init__(self, bot, full_config, instance):
        for i in 'client_id', 'access_token':
            if not i in instance:
                raise ValueError(
                    "Mastodon instance missing required configuration item %s: %r" % (
                        i, instance
                    )
                )
        for key in 'api_base_url', 'url':
            url = instance.get(key)
            if url:
                break
        if not url:
            url = "https://mastodon.social"
        self.api = Mastodon(
            client_id = instance['client_id'],
            client_secret = instance['client_secret'],
            access_token = instance['access_token'],
            api_base_url = url
        )

    def self_test(self):
        # Do something that will raise an exception if the credentials are invalid.
        # Return a string that will let the user know if they somehow gave
        # credentials to the wrong account.
        return self.api.account_verify_credentials()['username']
        
    def publish(self, post, publication):
        # If attachments the code looks something like this:
        # media = http://mastodon.media_post("image.png")
        # mastodon.status_post(slogan, media_ids=[media['id']])
        try:
            content = self.mastodon_safe(post.content)
            response = self.api.toot(content)
            publication.report_success()
        except Exception, e:
            set_trace()
            publication.report_failure(e)

    def mastodon_safe(self, content):
        # TODO: What counts as 'safe' depends on the mastodon instance and
        # in the worst case can require arbitrary plugins. But at least in
        # some cases the maximum length might be different.
        if isinstance(content, unicode):
            content = content.encode("utf8")
        return content[:500]


Publisher = MastodonPublisher
