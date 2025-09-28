"""
Users app serializers.

Django REST Framework serializers for user authentication,
registration, profile management, and JWT token handling.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles new user creation with password validation,
    email verification, and basic profile information.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm'
        )
        read_only_fields = ('id',)
    
    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value
    
    def validate_username(self, value):
        """Ensure username is unique and valid."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value
    
    def validate(self, attrs):
        """Validate password confirmation and strength."""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError(
                "Password and password confirmation do not match."
            )
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(
                {"password": list(e.messages)}
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create new user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Standard user serializer for retrieving and updating user data.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'username', 'is_active', 'date_joined', 'last_login')
    
    def get_full_name(self, obj):
        """Return user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
    current_password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name',
            'current_password', 'new_password', 'new_password_confirm'
        )
    
    def validate_email(self, value):
        """Ensure email is unique (excluding current user)."""
        user = self.instance
        if user and User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value
    
    def validate(self, attrs):
        """Validate password change if provided."""
        user = self.instance
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # If changing password, validate current password
        if new_password:
            if not current_password:
                raise serializers.ValidationError(
                    "Current password is required to change password."
                )
            
            if user and not user.check_password(current_password):
                raise serializers.ValidationError(
                    "Current password is incorrect."
                )
            
            if new_password != new_password_confirm:
                raise serializers.ValidationError(
                    "New passwords do not match."
                )
            
            # Validate new password strength
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                raise serializers.ValidationError(
                    {"new_password": list(e.messages)}
                )
        
        # Remove password confirmation fields from validated data
        attrs.pop('current_password', None)
        attrs.pop('new_password_confirm', None)
        
        return attrs
    
    def update(self, instance, validated_data):
        """Update user with optional password change."""
        new_password = validated_data.pop('new_password', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Change password if provided
        if new_password:
            instance.set_password(new_password)
        
        instance.save()
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user data.
    """
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to JWT token."""
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['full_name'] = f"{user.first_name} {user.last_name}".strip()
        
        return token
    
    def validate(self, attrs):
        """Add user data to token response."""
        data = super().validate(attrs)
        
        # Add user information to response
        if hasattr(self, 'user') and self.user:
            user_info = {
                'id': self.user.pk,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'full_name': f"{self.user.first_name} {self.user.last_name}".strip(),
            }
            # Type ignore to work around DRF response type inference
            data['user'] = user_info  # type: ignore
        
        return data


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Ensure user with email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user found with this email address."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate password confirmation and strength."""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                "Passwords do not match."
            )
        
        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError(
                {"new_password": list(e.messages)}
            )
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for extended user profile information.
    """
    user = UserSerializer(read_only=True)
    is_complete = serializers.ReadOnlyField()
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = (
            'id', 'user', 'phone', 'date_of_birth', 'bio',
            'avatar', 'address', 'city', 'country', 'postal_code',
            'newsletter_subscribed', 'marketing_emails_enabled',
            'is_complete', 'full_address', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_full_address(self, obj):
        """Return formatted full address."""
        return obj.get_full_address()


class UserListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for user lists (admin use).
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'full_name',
            'is_active', 'is_staff', 'date_joined'
        )
    
    def get_full_name(self, obj):
        """Return user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()