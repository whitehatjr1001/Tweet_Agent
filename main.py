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