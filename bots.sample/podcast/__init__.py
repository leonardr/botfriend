class PodcastBot(BasicBot):

    COLLECTION = "podcasts"

    def update_state(self):
        cutoff = self.model.last_state_update_time
        query = Audio.recent(
            "collection:%s" % self.COLLECTION, cutoff=cutoff, fields=[
                'createdate', 'title', 'identifier', 'publicdate', 'date',
                'creator', 'forumSubject', 'year',
                'avg_rating', 'downloads', 'language'
            ]
        )

        # Grab the 100 most recently posted podcasts.
        max_count = 100

        choices = []
        a = 0
        for audio in query:
            metadata = audio.metadata
            set_trace()
            a += 1
            if a > max_count:
                break
        
        self.json_state = choices
                
    def new_post(self):
        podcast = random.choice(self.model.json_state)
        
        # Create a post compatible with the PodcastPublisher.
        text = "%s\n\n%s" % (title, mp3_url)
        post,  is_new = PodcastPublisher.make_post(
            self.model, title, mp3_url, description,
        )
        return post

Bot = PodcastBot
