import tweepy
from app.models import Opportunity

class XListener:
    def __init__(self, api_key, api_secret):
        self.client = tweepy.Client(api_key, api_secret)
        self.keywords = [
            'hiring', 'recruitment', 'job opening',
            'talent acquisition', 'new position', 'career opportunity'
        ]
        
    def listen_for_opportunities(self):
        """
        Busca tweets relacionados con oportunidades de trabajo.
        """
        try:
            # Buscar tweets recientes
            tweets = self.client.search_recent_tweets(
                query=' OR '.join(self.keywords),
                max_results=100,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            # Procesar tweets
            opportunities = []
            for tweet in tweets.data:
                if self.is_relevant(tweet):
                    opportunities.append(self.extract_opportunity(tweet))
            
            return opportunities
        except Exception as e:
            return {'error': str(e)}
            
    def is_relevant(self, tweet):
        """Determina si un tweet es relevante."""
        return (
            tweet.public_metrics['retweet_count'] > 5 or
            tweet.public_metrics['like_count'] > 10
        )
        
    def extract_opportunity(self, tweet):
        """Extrae información de oportunidad de un tweet."""
        return {
            'source': 'x',
            'tweet_id': tweet.id,
            'text': tweet.text,
            'created_at': tweet.created_at,
            'metrics': tweet.public_metrics
        }
