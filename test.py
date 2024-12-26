import os

project_structure = {
    'bot': {
        '__init__.py': '',
        'twitter_handler.py': '''
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
''',
        'whatsapp_handler.py': '''
import os
from twilio.rest import Client

class WhatsAppHandler:
    def __init__(self):
        self.client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        self.admin_number = os.getenv('ADMIN_WHATSAPP_NUMBER')

    def send_message(self, to, body):
        self.client.messages.create(
            from_='whatsapp:' + self.whatsapp_number,
            body=body,
            to='whatsapp:' + to
        )

    def send_approval_request(self, draft_id, content):
        message = f"New tweet draft (ID: {draft_id}):\\n\\n{content}\\n\\nReply 'approve {draft_id}' to post or 'reject {draft_id}' to delete."
        self.send_message(self.admin_number, message)
''',
        'content_generator.py': '''
import random
import os
from google.cloud import aiplatform

class ContentGenerator:
    def __init__(self):
        self.content_bank = [
            "Excited about the latest developments in AI! #ArtificialIntelligence #TechTrends",
            "Machine Learning is revolutionizing industries. What's your take? #MachineLearning #Innovation",
            "The future of SaaS is bright! Are you ready for the next big thing? #SaaS #TechIndustry",
            "Cybersecurity should be a top priority for every business. Stay safe! #Cybersecurity #InfoSec"
        ]
        aiplatform.init(project=os.getenv('GCP_PROJECT_ID'))
        self.model = aiplatform.Model(model_name="gemini-1.5-pro-vision")

    def get_simple_tweet(self):
        return random.choice(self.content_bank)

    def generate_complex_tweet(self):
        prompt = "Generate a thoughtful tweet about recent advancements in AI and their potential impact on society. Include relevant hashtags."
        response = self.model.predict(instances=[{"prompt": prompt}])
        return response.predictions[0]
''',
        'analytics.py': '''
class AnalyticsManager:
    def __init__(self, twitter_handler):
        self.twitter_handler = twitter_handler

    def generate_weekly_report(self):
        metrics = self.twitter_handler.get_user_metrics()
        report = f"Weekly Twitter Analytics Report:\\n\\n"
        report += f"Followers: {metrics['followers_count']}\\n"
        report += f"Following: {metrics['following_count']}\\n"
        report += f"Tweet Count: {metrics['tweet_count']}\\n"
        report += f"Listed Count: {metrics['listed_count']}\\n"
        return report
'''
    },
    'main.py': '''
import os
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from bot.twitter_handler import TwitterHandler
from bot.whatsapp_handler import WhatsAppHandler
from bot.content_generator import ContentGenerator
from bot.analytics import AnalyticsManager

app = Flask(__name__)

twitter_handler = TwitterHandler()
whatsapp_handler = WhatsAppHandler()
content_generator = ContentGenerator()
analytics_manager = AnalyticsManager(twitter_handler)

scheduler = BackgroundScheduler()
scheduler.start()

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    sender = request.values.get('From', '')
    
    if incoming_msg.startswith('approve'):
        tweet_id = incoming_msg.split(' ')[1]
        twitter_handler.post_approved_tweet(tweet_id)
        whatsapp_handler.send_message(sender, f"Tweet {tweet_id} has been posted.")
    elif incoming_msg.startswith('reject'):
        tweet_id = incoming_msg.split(' ')[1]
        twitter_handler.delete_draft_tweet(tweet_id)
        whatsapp_handler.send_message(sender, f"Tweet {tweet_id} has been rejected and deleted.")
    
    return '', 200

@scheduler.scheduled_job('cron', hour='12')
def scheduled_tweet():
    simple_tweet = content_generator.get_simple_tweet()
    draft_id = twitter_handler.create_draft_tweet(simple_tweet)
    whatsapp_handler.send_approval_request(draft_id, simple_tweet)

@scheduler.scheduled_job('cron', hour='15')
def complex_tweet():
    complex_tweet = content_generator.generate_complex_tweet()
    draft_id = twitter_handler.create_draft_tweet(complex_tweet)
    whatsapp_handler.send_approval_request(draft_id, complex_tweet)

@scheduler.scheduled_job('cron', day_of_week='mon')
def weekly_analytics():
    report = analytics_manager.generate_weekly_report()
    whatsapp_handler.send_message(os.getenv('ADMIN_WHATSAPP_NUMBER'), report)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
''',
    'Dockerfile': '''
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
''',
    'requirements.txt': '''
Flask==2.0.1
twilio==7.8.0
tweepy==4.8.0
google-cloud-secret-manager==2.7.0
google-cloud-aiplatform==1.12.1
APScheduler==3.7.0
'''
}

def create_file(path, content):
    with open(path, 'w') as f:
        f.write(content.strip())

def create_project_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_project_structure(path, content)
        else:
            create_file(path, content)

if __name__ == '__main__':
    base_path = 'project_root'
    os.makedirs(base_path, exist_ok=True)
    create_project_structure(base_path, project_structure)
    print(f"Project structure created in '{base_path}' directory.")