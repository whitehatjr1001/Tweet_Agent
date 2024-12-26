import os
from tweepy import Client

class TwitterHandler:
    def __init__(self):
        self.client = Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        self.draft_tweets = {}

    def create_draft_tweet(self, content):
        draft_id = str(len(self.draft_tweets) + 1)
        self.draft_tweets[draft_id] = content
        return draft_id

    def post_approved_tweet(self, draft_id):
        if draft_id in self.draft_tweets:
            content = self.draft_tweets[draft_id]
            response = self.client.create_tweet(text=content)
            del self.draft_tweets[draft_id]
            return response.data['id']
        return None

    def delete_draft_tweet(self, draft_id):
        if draft_id in self.draft_tweets:
            del self.draft_tweets[draft_id]

    def get_user_metrics(self):
        user = self.client.get_me()
        user_id = user.data.id
        metrics = self.client.get_user(id=user_id, user_fields=['public_metrics'])
        return metrics.data.public_metrics