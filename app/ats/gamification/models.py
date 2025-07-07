"""Gamification models for ATS system."""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from app.models import Badge

User = get_user_model()


# Badge model is already defined in app.models.py
# This is just a reference to avoid import conflicts


class UserBadge(models.Model):
    """User badge assignment model."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_assignments')
    earned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ats_gamification_user_badge'
        verbose_name = 'User Badge'
        verbose_name_plural = 'User Badges'
        unique_together = ['user', 'badge']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}" 