"""
HuntRED® v2 - ML Sentiment Analysis System
Advanced sentiment analysis for employee feedback and social media
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter
import pickle
import os

# ML Libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.pipeline import Pipeline
    from textblob import TextBlob
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import SnowballStemmer
except ImportError:
    # Fallback for environments without ML libraries
    pass

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Advanced sentiment analysis system for HR applications"""
    
    def __init__(self, language='spanish'):
        self.language = language
        self.models = {}
        self.vectorizers = {}
        self.stemmer = None
        self.stop_words = set()
        
        # Initialize NLTK components
        self._initialize_nltk()
        
        # Load pre-trained models if available
        self._load_models()
        
        # HR-specific sentiment keywords
        self.hr_keywords = {
            'positive': [
                'excelente', 'bueno', 'satisfecho', 'feliz', 'motivado',
                'agradecido', 'orgulloso', 'cómodo', 'valorado', 'reconocido',
                'apoyo', 'crecimiento', 'oportunidad', 'balance', 'equipo',
                'liderazgo', 'innovación', 'aprendizaje', 'desarrollo'
            ],
            'negative': [
                'terrible', 'malo', 'insatisfecho', 'triste', 'desmotivado',
                'frustrado', 'estresado', 'sobrecargado', 'ignorado', 'subvalorado',
                'burnout', 'agotado', 'conflicto', 'presión', 'injusto',
                'discriminación', 'acoso', 'micromanagement', 'tóxico'
            ],
            'neutral': [
                'normal', 'regular', 'estándar', 'promedio', 'típico',
                'usual', 'común', 'rutinario', 'ordinario'
            ]
        }
    
    def _initialize_nltk(self):
        """Initialize NLTK components"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            
            if self.language == 'spanish':
                self.stop_words = set(stopwords.words('spanish'))
                self.stemmer = SnowballStemmer('spanish')
            else:
                self.stop_words = set(stopwords.words('english'))
                self.stemmer = SnowballStemmer('english')
                
            logger.info("NLTK components initialized successfully")
        except Exception as e:
            logger.warning(f"NLTK initialization failed: {e}")
            # Fallback stop words
            self.stop_words = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se'}
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        model_path = "models/sentiment/"
        if os.path.exists(model_path):
            try:
                # Load models
                for model_file in os.listdir(model_path):
                    if model_file.endswith('.pkl'):
                        model_name = model_file.replace('.pkl', '')
                        with open(os.path.join(model_path, model_file), 'rb') as f:
                            self.models[model_name] = pickle.load(f)
                
                logger.info(f"Loaded {len(self.models)} pre-trained models")
            except Exception as e:
                logger.warning(f"Failed to load models: {e}")
    
    def preprocess_text(self, text: str) -> str:
        """Advanced text preprocessing for sentiment analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove mentions and hashtags (social media)
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters but keep accented characters
        text = re.sub(r'[^\w\sáéíóúñü]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Tokenize and remove stop words
        try:
            tokens = word_tokenize(text)
            tokens = [self.stemmer.stem(token) for token in tokens 
                     if token not in self.stop_words and len(token) > 2]
            return ' '.join(tokens)
        except:
            # Fallback tokenization
            words = text.split()
            words = [word for word in words if word not in self.stop_words and len(word) > 2]
            return ' '.join(words)
    
    def analyze_sentiment_basic(self, text: str) -> Dict[str, Any]:
        """Basic sentiment analysis using keyword matching"""
        if not text:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'score': 0.0}
        
        text_lower = text.lower()
        
        # Count sentiment keywords
        positive_count = sum(1 for word in self.hr_keywords['positive'] if word in text_lower)
        negative_count = sum(1 for word in self.hr_keywords['negative'] if word in text_lower)
        neutral_count = sum(1 for word in self.hr_keywords['neutral'] if word in text_lower)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return {'sentiment': 'neutral', 'confidence': 0.5, 'score': 0.0}
        
        # Calculate sentiment scores
        positive_ratio = positive_count / total_sentiment_words
        negative_ratio = negative_count / total_sentiment_words
        
        # Determine sentiment
        if positive_ratio > negative_ratio:
            sentiment = 'positive'
            confidence = positive_ratio
            score = positive_ratio - negative_ratio
        elif negative_ratio > positive_ratio:
            sentiment = 'negative'
            confidence = negative_ratio
            score = -(negative_ratio - positive_ratio)
        else:
            sentiment = 'neutral'
            confidence = 0.5
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': score,
            'positive_words': positive_count,
            'negative_words': negative_count,
            'total_words': len(text_lower.split())
        }
    
    def analyze_sentiment_textblob(self, text: str) -> Dict[str, Any]:
        """Sentiment analysis using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Map polarity to sentiment
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'confidence': abs(polarity),
                'score': polarity,
                'subjectivity': subjectivity
            }
        except Exception as e:
            logger.warning(f"TextBlob analysis failed: {e}")
            return self.analyze_sentiment_basic(text)
    
    def analyze_sentiment_ml(self, text: str, model_name: str = 'default') -> Dict[str, Any]:
        """ML-based sentiment analysis using trained models"""
        if model_name not in self.models:
            logger.warning(f"Model {model_name} not found, using basic analysis")
            return self.analyze_sentiment_basic(text)
        
        try:
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            # Get model and vectorizer
            model = self.models[model_name]
            vectorizer = self.vectorizers.get(model_name)
            
            if vectorizer is None:
                logger.warning(f"Vectorizer for {model_name} not found")
                return self.analyze_sentiment_basic(text)
            
            # Vectorize text
            text_vector = vectorizer.transform([processed_text])
            
            # Predict sentiment
            prediction = model.predict(text_vector)[0]
            confidence = max(model.predict_proba(text_vector)[0])
            
            # Map prediction to sentiment
            sentiment_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
            sentiment = sentiment_map.get(prediction, 'neutral')
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'score': confidence if sentiment == 'positive' else -confidence if sentiment == 'negative' else 0,
                'model_used': model_name
            }
            
        except Exception as e:
            logger.error(f"ML sentiment analysis failed: {e}")
            return self.analyze_sentiment_basic(text)
    
    def analyze_sentiment_comprehensive(self, text: str) -> Dict[str, Any]:
        """Comprehensive sentiment analysis using multiple methods"""
        results = {}
        
        # Basic keyword analysis
        results['basic'] = self.analyze_sentiment_basic(text)
        
        # TextBlob analysis
        results['textblob'] = self.analyze_sentiment_textblob(text)
        
        # ML analysis if available
        if self.models:
            results['ml'] = self.analyze_sentiment_ml(text)
        
        # Ensemble prediction
        sentiments = [r['sentiment'] for r in results.values()]
        scores = [r['score'] for r in results.values()]
        
        # Most common sentiment
        sentiment_counter = Counter(sentiments)
        final_sentiment = sentiment_counter.most_common(1)[0][0]
        
        # Average score
        final_score = np.mean(scores) if scores else 0.0
        
        # Average confidence
        confidences = [r['confidence'] for r in results.values()]
        final_confidence = np.mean(confidences) if confidences else 0.5
        
        return {
            'sentiment': final_sentiment,
            'confidence': final_confidence,
            'score': final_score,
            'methods_used': list(results.keys()),
            'individual_results': results,
            'consensus_strength': sentiment_counter[final_sentiment] / len(sentiments)
        }
    
    def analyze_employee_feedback(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of employee feedback and surveys"""
        if not feedback_data:
            return {'error': 'No feedback data provided'}
        
        results = {
            'total_feedback': len(feedback_data),
            'sentiment_distribution': defaultdict(int),
            'average_score': 0.0,
            'department_analysis': defaultdict(list),
            'time_analysis': defaultdict(list),
            'detailed_results': []
        }
        
        total_score = 0.0
        
        for feedback in feedback_data:
            text = feedback.get('text', '')
            employee_id = feedback.get('employee_id')
            department = feedback.get('department', 'Unknown')
            timestamp = feedback.get('timestamp', datetime.now())
            
            # Analyze sentiment
            analysis = self.analyze_sentiment_comprehensive(text)
            
            # Update results
            sentiment = analysis['sentiment']
            score = analysis['score']
            
            results['sentiment_distribution'][sentiment] += 1
            results['department_analysis'][department].append(analysis)
            
            # Group by time period (month)
            time_key = timestamp.strftime('%Y-%m') if isinstance(timestamp, datetime) else 'unknown'
            results['time_analysis'][time_key].append(analysis)
            
            total_score += score
            
            # Store detailed result
            results['detailed_results'].append({
                'employee_id': employee_id,
                'department': department,
                'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                'text': text[:100] + '...' if len(text) > 100 else text,
                'analysis': analysis
            })
        
        # Calculate averages
        results['average_score'] = total_score / len(feedback_data)
        
        # Department summaries
        dept_summaries = {}
        for dept, analyses in results['department_analysis'].items():
            dept_sentiments = [a['sentiment'] for a in analyses]
            dept_scores = [a['score'] for a in analyses]
            
            dept_summaries[dept] = {
                'total_feedback': len(analyses),
                'sentiment_distribution': dict(Counter(dept_sentiments)),
                'average_score': np.mean(dept_scores),
                'dominant_sentiment': Counter(dept_sentiments).most_common(1)[0][0]
            }
        
        results['department_summaries'] = dept_summaries
        
        # Time trend analysis
        time_summaries = {}
        for period, analyses in results['time_analysis'].items():
            period_scores = [a['score'] for a in analyses]
            period_sentiments = [a['sentiment'] for a in analyses]
            
            time_summaries[period] = {
                'average_score': np.mean(period_scores),
                'sentiment_distribution': dict(Counter(period_sentiments)),
                'feedback_count': len(analyses)
            }
        
        results['time_trends'] = time_summaries
        
        return results
    
    def train_custom_model(self, training_data: List[Dict[str, Any]], model_name: str = 'custom') -> Dict[str, Any]:
        """Train a custom sentiment analysis model"""
        try:
            # Prepare data
            texts = []
            labels = []
            
            for item in training_data:
                text = item.get('text', '')
                sentiment = item.get('sentiment', 'neutral')
                
                if text and sentiment:
                    texts.append(self.preprocess_text(text))
                    # Map sentiment to numeric label
                    label_map = {'negative': 0, 'neutral': 1, 'positive': 2}
                    labels.append(label_map.get(sentiment, 1))
            
            if len(texts) < 10:
                return {'error': 'Insufficient training data (minimum 10 samples required)'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            # Create pipeline
            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            classifier = LogisticRegression(random_state=42)
            
            pipeline = Pipeline([
                ('vectorizer', vectorizer),
                ('classifier', classifier)
            ])
            
            # Train model
            pipeline.fit(X_train, y_train)
            
            # Evaluate
            y_pred = pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            self.models[model_name] = pipeline
            self.vectorizers[model_name] = vectorizer
            
            # Save to disk
            os.makedirs('models/sentiment', exist_ok=True)
            with open(f'models/sentiment/{model_name}.pkl', 'wb') as f:
                pickle.dump(pipeline, f)
            
            return {
                'success': True,
                'model_name': model_name,
                'accuracy': accuracy,
                'training_samples': len(texts),
                'test_samples': len(X_test),
                'classification_report': classification_report(y_test, y_pred, output_dict=True)
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {'error': str(e)}
    
    def get_sentiment_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from sentiment analysis"""
        insights = {
            'recommendations': [],
            'alerts': [],
            'trends': [],
            'action_items': []
        }
        
        # Overall sentiment health
        avg_score = analysis_results.get('average_score', 0)
        
        if avg_score < -0.3:
            insights['alerts'].append({
                'type': 'critical',
                'message': 'Overall employee sentiment is significantly negative',
                'priority': 'high',
                'action': 'Immediate management attention required'
            })
        elif avg_score < -0.1:
            insights['alerts'].append({
                'type': 'warning',
                'message': 'Employee sentiment trending negative',
                'priority': 'medium',
                'action': 'Review recent changes and policies'
            })
        
        # Department analysis
        dept_summaries = analysis_results.get('department_summaries', {})
        for dept, summary in dept_summaries.items():
            dept_score = summary.get('average_score', 0)
            
            if dept_score < -0.2:
                insights['recommendations'].append({
                    'department': dept,
                    'issue': 'Low sentiment score',
                    'recommendation': f'Focus on {dept} department - conduct team meetings and address concerns',
                    'priority': 'high'
                })
        
        # Time trends
        time_trends = analysis_results.get('time_trends', {})
        if len(time_trends) >= 2:
            periods = sorted(time_trends.keys())
            recent_scores = [time_trends[p]['average_score'] for p in periods[-3:]]
            
            if len(recent_scores) >= 2:
                trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
                
                if trend < -0.1:
                    insights['trends'].append({
                        'type': 'declining',
                        'message': 'Employee sentiment is declining over time',
                        'trend_value': trend,
                        'action': 'Investigate recent organizational changes'
                    })
                elif trend > 0.1:
                    insights['trends'].append({
                        'type': 'improving',
                        'message': 'Employee sentiment is improving over time',
                        'trend_value': trend,
                        'action': 'Continue current positive initiatives'
                    })
        
        # Action items based on sentiment distribution
        sentiment_dist = analysis_results.get('sentiment_distribution', {})
        total_feedback = sum(sentiment_dist.values())
        
        if total_feedback > 0:
            negative_ratio = sentiment_dist.get('negative', 0) / total_feedback
            
            if negative_ratio > 0.4:
                insights['action_items'].append({
                    'priority': 'urgent',
                    'action': 'Employee satisfaction survey',
                    'description': 'High negative sentiment detected - conduct detailed survey',
                    'timeline': 'Within 1 week'
                })
            
            if negative_ratio > 0.6:
                insights['action_items'].append({
                    'priority': 'critical',
                    'action': 'Management intervention',
                    'description': 'Critical sentiment levels - immediate management action required',
                    'timeline': 'Immediately'
                })
        
        return insights

# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()

# Utility functions
def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """Quick sentiment analysis for a single text"""
    return sentiment_analyzer.analyze_sentiment_comprehensive(text)

def analyze_employee_feedback_batch(feedback_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Batch analysis of employee feedback"""
    return sentiment_analyzer.analyze_employee_feedback(feedback_list)

def get_hr_insights(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Get HR-specific insights from sentiment analysis"""
    return sentiment_analyzer.get_sentiment_insights(analysis_results)