"""Gamification services for ATS system."""

from django.contrib.auth import get_user_model
from .models import Badge, UserBadge

User = get_user_model()


class GamificationService:
    """Service for managing gamification features."""
    
    @staticmethod
    def award_badge(user, badge_name):
        """Award a badge to a user."""
        try:
            badge = Badge.objects.get(name=badge_name, is_active=True)
            user_badge, created = UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={'is_active': True}
            )
            return user_badge, created
        except Badge.DoesNotExist:
            return None, False
    
    @staticmethod
    def get_user_badges(user):
        """Get all badges for a user."""
        return UserBadge.objects.filter(user=user, is_active=True).select_related('badge')
    
    @staticmethod
    def get_user_points(user):
        """Calculate total points for a user."""
        user_badges = UserBadge.objects.filter(user=user, is_active=True).select_related('badge')
        return sum(ub.badge.points for ub in user_badges) 