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