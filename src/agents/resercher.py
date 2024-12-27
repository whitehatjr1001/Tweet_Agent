class AnalyticsManager:
    def __init__(self, twitter_handler):
        self.twitter_handler = twitter_handler

    def generate_weekly_report(self):
        metrics = self.twitter_handler.get_user_metrics()
        report = f"Weekly Twitter Analytics Report:\n\n"
        report += f"Followers: {metrics['followers_count']}\n"
        report += f"Following: {metrics['following_count']}\n"
        report += f"Tweet Count: {metrics['tweet_count']}\n"
        report += f"Listed Count: {metrics['listed_count']}\n"
        return report