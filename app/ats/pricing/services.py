"""Pricing services for ATS system."""

from django.contrib.auth import get_user_model
from .models import Bundle

User = get_user_model()


class PricingService:
    """Service for managing pricing features."""
    
    @staticmethod
    def get_active_bundles():
        """Get all active bundles."""
        return Bundle.objects.filter(is_active=True).order_by('price')
    
    @staticmethod
    def get_bundle_by_id(bundle_id):
        """Get a specific bundle by ID."""
        try:
            return Bundle.objects.get(id=bundle_id, is_active=True)
        except Bundle.DoesNotExist:
            return None
    
    @staticmethod
    def calculate_bundle_price(bundle, quantity=1):
        """Calculate the total price for a bundle with quantity."""
        return bundle.price * quantity 