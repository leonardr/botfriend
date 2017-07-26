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
        self.instance = Mastodon(
            client_id = instance['client_id'],
            client_secret = instance['client_secret'],
            access_token = instance['access_token'],
            api_base_url = url
        )

    def publish(self, post, publication):
        media_ids = []
        for attachment in post.attachments:
            if attachment.filename:
                arguments = dict(media_file=attachment.filename)
            else:
                arguments = dict(media_file=attachment.contents,
                                 mime_type=attachment.media_type)
            media = self.instance.media_post(**arguments)
            media_ids.append(media['id'])
        try:
            content = self.mastodon_safe(post.content)
            response = self.instance.status_post(
                content, media_ids=media_ids, sensitive=post.sensitive
            )
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
