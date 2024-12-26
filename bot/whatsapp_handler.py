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
        message = f"New tweet draft (ID: {draft_id}):\n\n{content}\n\nReply 'approve {draft_id}' to post or 'reject {draft_id}' to delete."
        self.send_message(self.admin_number, message)