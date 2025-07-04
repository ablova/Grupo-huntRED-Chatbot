"""
🚀 GhuntRED-v2 Core Serializers
API serializers for authentication and user management
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """User serializer for API responses"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'birth_date', 'profile_picture', 'bio',
            'country', 'state', 'city', 'linkedin_url', 'github_url',
            'portfolio_url', 'business_unit', 'email_verified',
            'phone_verified', 'show_email', 'show_phone',
            'created_at', 'updated_at', 'has_complete_profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'has_complete_profile']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'country', 'state', 'city'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """User profile update serializer"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'birth_date',
            'profile_picture', 'bio', 'country', 'state', 'city',
            'linkedin_url', 'github_url', 'portfolio_url',
            'show_email', 'show_phone'
        ]