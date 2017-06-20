from bot import Publisher

class MastodonPublisher(Publisher):
    def __init__(self, *args, **kwargs):
        pass

Publisher = MastodonPublisher
