"""
HuntRED® v2 - SocialLink Engine
Advanced social media analysis and employee social presence monitoring
"""

import re
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass
import hashlib

# Social Media APIs (with fallbacks)
try:
    import tweepy
    import facebook
    import linkedin_api
    SOCIAL_APIS_AVAILABLE = True
except ImportError:
    SOCIAL_APIS_AVAILABLE = False

from sqlalchemy.orm import Session
from ..database.models import Employee, Company
from ..ml.sentiment_analysis import sentiment_analyzer

logger = logging.getLogger(__name__)

@dataclass
class SocialProfile:
    """Social media profile data structure"""
    platform: str
    username: str
    url: str
    followers_count: int
    following_count: int
    posts_count: int
    verified: bool
    bio: str
    profile_image_url: str
    last_activity: datetime
    engagement_rate: float
    sentiment_score: float

@dataclass
class SocialPost:
    """Social media post data structure"""
    platform: str
    post_id: str
    username: str
    content: str
    timestamp: datetime
    likes_count: int
    shares_count: int
    comments_count: int
    hashtags: List[str]
    mentions: List[str]
    sentiment_score: float
    engagement_rate: float
    reach: int

class SocialMediaAnalyzer:
    """Advanced social media analysis engine"""
    
    def __init__(self):
        self.platforms = {
            'twitter': TwitterAnalyzer(),
            'linkedin': LinkedInAnalyzer(),
            'facebook': FacebookAnalyzer(),
            'instagram': InstagramAnalyzer()
        }
        
        # Keywords for HR-related content detection
        self.hr_keywords = {
            'job_search': [
                'buscando trabajo', 'busco empleo', 'looking for job', 'job hunting',
                'desempleado', 'unemployed', 'seeking opportunity', 'career change',
                'nuevo trabajo', 'new job', 'job interview', 'entrevista trabajo'
            ],
            'company_sentiment': [
                'mi empresa', 'my company', 'trabajo en', 'work at',
                'mi jefe', 'my boss', 'compañeros trabajo', 'coworkers',
                'ambiente laboral', 'work environment', 'cultura empresa'
            ],
            'burnout_indicators': [
                'agotado', 'exhausted', 'burnout', 'estresado', 'stressed',
                'sobrecargado', 'overworked', 'no puedo más', 'cant take it',
                'necesito vacaciones', 'need vacation', 'work life balance'
            ],
            'career_growth': [
                'promoción', 'promotion', 'ascenso', 'new role', 'nuevo puesto',
                'desarrollo profesional', 'professional development',
                'certificación', 'certification', 'curso', 'training'
            ]
        }
        
        # Risk indicators
        self.risk_indicators = {
            'high_risk': [
                'renuncio', 'quitting', 'leaving job', 'último día',
                'new opportunity', 'nueva oportunidad', 'farewell',
                'despedida', 'moving on', 'siguiente capítulo'
            ],
            'medium_risk': [
                'pensando cambiar', 'thinking about change', 'evaluating options',
                'explorando opciones', 'considering offers', 'job market'
            ],
            'positive_indicators': [
                'amo mi trabajo', 'love my job', 'great team', 'excelente equipo',
                'proud to work', 'orgulloso trabajar', 'amazing company'
            ]
        }
    
    async def analyze_employee_social_presence(self, employee_id: str, db: Session) -> Dict[str, Any]:
        """Comprehensive social media analysis for an employee"""
        try:
            # Get employee data
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return {'error': 'Employee not found'}
            
            # Search for social profiles
            profiles = await self._find_employee_profiles(employee)
            
            # Analyze each platform
            analysis_results = {}
            overall_sentiment = 0.0
            total_engagement = 0.0
            risk_score = 0.0
            
            for platform, profile in profiles.items():
                if profile:
                    platform_analysis = await self._analyze_platform(platform, profile)
                    analysis_results[platform] = platform_analysis
                    
                    # Aggregate metrics
                    overall_sentiment += platform_analysis.get('sentiment_score', 0)
                    total_engagement += platform_analysis.get('engagement_rate', 0)
                    risk_score += platform_analysis.get('risk_score', 0)
            
            # Calculate overall metrics
            platform_count = len(analysis_results)
            if platform_count > 0:
                overall_sentiment /= platform_count
                total_engagement /= platform_count
                risk_score /= platform_count
            
            # Generate insights
            insights = self._generate_social_insights(analysis_results, employee)
            
            return {
                'employee_id': employee_id,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'analysis_date': datetime.now().isoformat(),
                'platforms_analyzed': list(analysis_results.keys()),
                'overall_metrics': {
                    'sentiment_score': overall_sentiment,
                    'engagement_rate': total_engagement,
                    'risk_score': risk_score,
                    'social_presence_strength': self._calculate_presence_strength(profiles)
                },
                'platform_analysis': analysis_results,
                'insights': insights,
                'recommendations': self._generate_recommendations(insights, risk_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing social presence for employee {employee_id}: {e}")
            return {'error': str(e)}
    
    async def _find_employee_profiles(self, employee: Employee) -> Dict[str, Optional[SocialProfile]]:
        """Find employee social media profiles"""
        profiles = {}
        
        # Generate search queries
        search_queries = [
            f"{employee.first_name} {employee.last_name}",
            f"{employee.first_name}.{employee.last_name}",
            f"{employee.first_name}_{employee.last_name}",
            employee.email.split('@')[0] if employee.email else None
        ]
        
        # Search each platform
        for platform_name, analyzer in self.platforms.items():
            try:
                profile = await analyzer.search_profile(search_queries, employee)
                profiles[platform_name] = profile
            except Exception as e:
                logger.warning(f"Failed to search {platform_name} for {employee.first_name}: {e}")
                profiles[platform_name] = None
        
        return profiles
    
    async def _analyze_platform(self, platform: str, profile: SocialProfile) -> Dict[str, Any]:
        """Analyze specific social media platform"""
        analyzer = self.platforms.get(platform)
        if not analyzer:
            return {}
        
        try:
            # Get recent posts
            recent_posts = await analyzer.get_recent_posts(profile.username, limit=50)
            
            # Analyze posts
            post_analysis = self._analyze_posts(recent_posts)
            
            # Calculate platform metrics
            return {
                'profile': {
                    'username': profile.username,
                    'followers': profile.followers_count,
                    'following': profile.following_count,
                    'posts_count': profile.posts_count,
                    'verified': profile.verified,
                    'engagement_rate': profile.engagement_rate
                },
                'content_analysis': post_analysis,
                'sentiment_score': post_analysis.get('overall_sentiment', 0),
                'risk_score': post_analysis.get('risk_score', 0),
                'activity_level': self._calculate_activity_level(recent_posts),
                'professional_score': self._calculate_professional_score(recent_posts, profile)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {platform} platform: {e}")
            return {}
    
    def _analyze_posts(self, posts: List[SocialPost]) -> Dict[str, Any]:
        """Analyze social media posts for HR insights"""
        if not posts:
            return {
                'total_posts': 0,
                'overall_sentiment': 0.0,
                'risk_score': 0.0,
                'content_categories': {}
            }
        
        sentiment_scores = []
        risk_indicators_found = []
        content_categories = defaultdict(int)
        
        for post in posts:
            # Sentiment analysis
            sentiment_result = sentiment_analyzer.analyze_sentiment_comprehensive(post.content)
            sentiment_scores.append(sentiment_result['score'])
            
            # Check for risk indicators
            content_lower = post.content.lower()
            
            for risk_level, indicators in self.risk_indicators.items():
                for indicator in indicators:
                    if indicator in content_lower:
                        risk_indicators_found.append((risk_level, indicator))
            
            # Categorize content
            for category, keywords in self.hr_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        content_categories[category] += 1
                        break
        
        # Calculate overall metrics
        overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(risk_indicators_found)
        
        return {
            'total_posts': len(posts),
            'overall_sentiment': overall_sentiment,
            'risk_score': risk_score,
            'content_categories': dict(content_categories),
            'risk_indicators': risk_indicators_found,
            'sentiment_distribution': self._categorize_sentiments(sentiment_scores)
        }
    
    def _calculate_risk_score(self, risk_indicators: List[Tuple[str, str]]) -> float:
        """Calculate employee risk score based on social media indicators"""
        risk_weights = {
            'high_risk': 0.8,
            'medium_risk': 0.4,
            'positive_indicators': -0.3
        }
        
        total_risk = 0.0
        for risk_level, _ in risk_indicators:
            total_risk += risk_weights.get(risk_level, 0)
        
        # Normalize to 0-1 range
        return max(0, min(1, total_risk))
    
    def _calculate_activity_level(self, posts: List[SocialPost]) -> str:
        """Calculate social media activity level"""
        if not posts:
            return 'inactive'
        
        # Posts in last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_posts = [p for p in posts if p.timestamp >= thirty_days_ago]
        
        posts_per_week = len(recent_posts) / 4.3  # Approximate weeks in a month
        
        if posts_per_week >= 5:
            return 'very_active'
        elif posts_per_week >= 2:
            return 'active'
        elif posts_per_week >= 0.5:
            return 'moderate'
        else:
            return 'low'
    
    def _calculate_professional_score(self, posts: List[SocialPost], profile: SocialProfile) -> float:
        """Calculate how professional the social media presence is"""
        if not posts:
            return 0.5
        
        professional_indicators = [
            'career', 'professional', 'industry', 'networking',
            'conference', 'learning', 'development', 'achievement',
            'certification', 'skills', 'expertise', 'leadership'
        ]
        
        professional_posts = 0
        total_posts = len(posts)
        
        for post in posts:
            content_lower = post.content.lower()
            if any(indicator in content_lower for indicator in professional_indicators):
                professional_posts += 1
        
        # Base score from content
        content_score = professional_posts / total_posts if total_posts > 0 else 0
        
        # Adjust based on profile characteristics
        profile_score = 0.5
        if profile.verified:
            profile_score += 0.2
        if 'professional' in profile.bio.lower() or 'ceo' in profile.bio.lower():
            profile_score += 0.1
        
        # Combined score
        return min(1.0, (content_score * 0.7) + (profile_score * 0.3))
    
    def _categorize_sentiments(self, sentiment_scores: List[float]) -> Dict[str, int]:
        """Categorize sentiment scores"""
        categories = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for score in sentiment_scores:
            if score > 0.1:
                categories['positive'] += 1
            elif score < -0.1:
                categories['negative'] += 1
            else:
                categories['neutral'] += 1
        
        return categories
    
    def _calculate_presence_strength(self, profiles: Dict[str, Optional[SocialProfile]]) -> float:
        """Calculate overall social media presence strength"""
        active_profiles = [p for p in profiles.values() if p is not None]
        
        if not active_profiles:
            return 0.0
        
        # Base score from number of platforms
        platform_score = len(active_profiles) / 4  # Max 4 platforms
        
        # Weighted by follower counts
        total_followers = sum(p.followers_count for p in active_profiles)
        follower_score = min(1.0, total_followers / 10000)  # Normalize to 10k followers
        
        # Weighted by engagement
        avg_engagement = sum(p.engagement_rate for p in active_profiles) / len(active_profiles)
        
        return (platform_score * 0.4) + (follower_score * 0.3) + (avg_engagement * 0.3)
    
    def _generate_social_insights(self, analysis_results: Dict[str, Any], employee: Employee) -> Dict[str, Any]:
        """Generate actionable insights from social media analysis"""
        insights = {
            'strengths': [],
            'concerns': [],
            'opportunities': [],
            'risk_factors': []
        }
        
        # Analyze across platforms
        for platform, analysis in analysis_results.items():
            if not analysis:
                continue
            
            risk_score = analysis.get('risk_score', 0)
            sentiment_score = analysis.get('sentiment_score', 0)
            professional_score = analysis.get('professional_score', 0.5)
            
            # Identify strengths
            if professional_score > 0.7:
                insights['strengths'].append(f"Strong professional presence on {platform}")
            
            if sentiment_score > 0.3:
                insights['strengths'].append(f"Positive sentiment on {platform}")
            
            # Identify concerns
            if risk_score > 0.6:
                insights['concerns'].append(f"High risk indicators detected on {platform}")
            
            if sentiment_score < -0.3:
                insights['concerns'].append(f"Negative sentiment pattern on {platform}")
            
            # Identify opportunities
            if professional_score < 0.3:
                insights['opportunities'].append(f"Could improve professional branding on {platform}")
            
            # Risk factors
            content_analysis = analysis.get('content_analysis', {})
            risk_indicators = content_analysis.get('risk_indicators', [])
            
            for risk_level, indicator in risk_indicators:
                if risk_level == 'high_risk':
                    insights['risk_factors'].append(f"High risk: '{indicator}' mentioned on {platform}")
                elif risk_level == 'medium_risk':
                    insights['risk_factors'].append(f"Medium risk: '{indicator}' mentioned on {platform}")
        
        return insights
    
    def _generate_recommendations(self, insights: Dict[str, Any], overall_risk_score: float) -> List[Dict[str, str]]:
        """Generate HR recommendations based on social media analysis"""
        recommendations = []
        
        # High risk recommendations
        if overall_risk_score > 0.7:
            recommendations.append({
                'priority': 'urgent',
                'category': 'Retention',
                'action': 'Immediate check-in meeting',
                'description': 'High risk indicators detected in social media - schedule urgent one-on-one',
                'timeline': 'Within 24 hours'
            })
        
        elif overall_risk_score > 0.4:
            recommendations.append({
                'priority': 'high',
                'category': 'Engagement',
                'action': 'Schedule career discussion',
                'description': 'Medium risk indicators - discuss career satisfaction and goals',
                'timeline': 'Within 1 week'
            })
        
        # Concerns-based recommendations
        if insights['concerns']:
            recommendations.append({
                'priority': 'medium',
                'category': 'Monitoring',
                'action': 'Increased monitoring',
                'description': 'Continue monitoring social media presence for changes',
                'timeline': 'Ongoing'
            })
        
        # Opportunity-based recommendations
        if insights['opportunities']:
            recommendations.append({
                'priority': 'low',
                'category': 'Development',
                'action': 'Professional branding training',
                'description': 'Offer training on professional social media presence',
                'timeline': 'Next quarter'
            })
        
        return recommendations

class TwitterAnalyzer:
    """Twitter-specific analysis"""
    
    async def search_profile(self, search_queries: List[str], employee: Employee) -> Optional[SocialProfile]:
        """Search for Twitter profile"""
        # Mock implementation - replace with real Twitter API
        return SocialProfile(
            platform='twitter',
            username=f"{employee.first_name.lower()}_{employee.last_name.lower()}",
            url=f"https://twitter.com/{employee.first_name.lower()}_{employee.last_name.lower()}",
            followers_count=150,
            following_count=200,
            posts_count=45,
            verified=False,
            bio=f"Professional at {employee.department}",
            profile_image_url="",
            last_activity=datetime.now(),
            engagement_rate=0.03,
            sentiment_score=0.1
        )
    
    async def get_recent_posts(self, username: str, limit: int = 50) -> List[SocialPost]:
        """Get recent Twitter posts"""
        # Mock implementation
        return [
            SocialPost(
                platform='twitter',
                post_id='123456',
                username=username,
                content="Great day at work! Learning new technologies.",
                timestamp=datetime.now() - timedelta(days=1),
                likes_count=5,
                shares_count=1,
                comments_count=2,
                hashtags=['work', 'learning'],
                mentions=[],
                sentiment_score=0.6,
                engagement_rate=0.04,
                reach=100
            )
        ]

class LinkedInAnalyzer:
    """LinkedIn-specific analysis"""
    
    async def search_profile(self, search_queries: List[str], employee: Employee) -> Optional[SocialProfile]:
        """Search for LinkedIn profile"""
        return SocialProfile(
            platform='linkedin',
            username=f"{employee.first_name}-{employee.last_name}",
            url=f"https://linkedin.com/in/{employee.first_name}-{employee.last_name}",
            followers_count=500,
            following_count=300,
            posts_count=20,
            verified=False,
            bio=f"{employee.position} at {employee.department}",
            profile_image_url="",
            last_activity=datetime.now(),
            engagement_rate=0.08,
            sentiment_score=0.3
        )
    
    async def get_recent_posts(self, username: str, limit: int = 50) -> List[SocialPost]:
        """Get recent LinkedIn posts"""
        return [
            SocialPost(
                platform='linkedin',
                post_id='789012',
                username=username,
                content="Excited about our new project launch. Team collaboration at its best!",
                timestamp=datetime.now() - timedelta(days=3),
                likes_count=15,
                shares_count=3,
                comments_count=8,
                hashtags=['teamwork', 'project'],
                mentions=[],
                sentiment_score=0.8,
                engagement_rate=0.12,
                reach=300
            )
        ]

class FacebookAnalyzer:
    """Facebook-specific analysis"""
    
    async def search_profile(self, search_queries: List[str], employee: Employee) -> Optional[SocialProfile]:
        """Search for Facebook profile"""
        return None  # Usually private
    
    async def get_recent_posts(self, username: str, limit: int = 50) -> List[SocialPost]:
        """Get recent Facebook posts"""
        return []  # Usually private

class InstagramAnalyzer:
    """Instagram-specific analysis"""
    
    async def search_profile(self, search_queries: List[str], employee: Employee) -> Optional[SocialProfile]:
        """Search for Instagram profile"""
        return SocialProfile(
            platform='instagram',
            username=f"{employee.first_name.lower()}{employee.last_name.lower()}",
            url=f"https://instagram.com/{employee.first_name.lower()}{employee.last_name.lower()}",
            followers_count=80,
            following_count=120,
            posts_count=35,
            verified=False,
            bio="",
            profile_image_url="",
            last_activity=datetime.now(),
            engagement_rate=0.06,
            sentiment_score=0.2
        )
    
    async def get_recent_posts(self, username: str, limit: int = 50) -> List[SocialPost]:
        """Get recent Instagram posts"""
        return []

# Global social media analyzer
social_analyzer = SocialMediaAnalyzer()

# Utility functions
async def analyze_employee_social_media(employee_id: str, db: Session) -> Dict[str, Any]:
    """Analyze employee social media presence"""
    return await social_analyzer.analyze_employee_social_presence(employee_id, db)

async def monitor_company_social_sentiment(company_id: str, db: Session) -> Dict[str, Any]:
    """Monitor social media sentiment for all company employees"""
    try:
        employees = db.query(Employee).filter(
            Employee.company_id == company_id,
            Employee.is_active == True
        ).all()
        
        results = {
            'company_id': company_id,
            'total_employees': len(employees),
            'analyzed_employees': 0,
            'high_risk_employees': [],
            'overall_sentiment': 0.0,
            'platform_summary': defaultdict(int)
        }
        
        total_sentiment = 0.0
        analyzed_count = 0
        
        for employee in employees:
            try:
                analysis = await analyze_employee_social_media(employee.id, db)
                
                if 'error' not in analysis:
                    analyzed_count += 1
                    overall_metrics = analysis.get('overall_metrics', {})
                    risk_score = overall_metrics.get('risk_score', 0)
                    sentiment = overall_metrics.get('sentiment_score', 0)
                    
                    total_sentiment += sentiment
                    
                    # Track high-risk employees
                    if risk_score > 0.6:
                        results['high_risk_employees'].append({
                            'employee_id': employee.id,
                            'name': f"{employee.first_name} {employee.last_name}",
                            'risk_score': risk_score,
                            'platforms': analysis.get('platforms_analyzed', [])
                        })
                    
                    # Count platforms
                    for platform in analysis.get('platforms_analyzed', []):
                        results['platform_summary'][platform] += 1
                        
            except Exception as e:
                logger.warning(f"Failed to analyze employee {employee.id}: {e}")
        
        results['analyzed_employees'] = analyzed_count
        results['overall_sentiment'] = total_sentiment / analyzed_count if analyzed_count > 0 else 0
        results['platform_summary'] = dict(results['platform_summary'])
        
        return results
        
    except Exception as e:
        logger.error(f"Error monitoring company social sentiment: {e}")
        return {'error': str(e)}