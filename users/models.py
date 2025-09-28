from django.db import models

"""
Users app models.

Custom user model and related profile models.
"""

import uuid
from typing import TYPE_CHECKING
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

if TYPE_CHECKING:
    from django.db.models import QuerySet


class User(AbstractUser):
    """
    Custom user model with email as the primary identifier.
    
    Extends Django's AbstractUser with additional fields and email-based authentication.
    """
    email = models.EmailField(unique=True)
    
    # Override username to make it optional
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters.'
            ),
        ],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    
    # Use email as the primary authentication field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_active']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_short_name(self):
        """Return the user's first name."""
        return self.first_name or self.username


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Personal information
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Address information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Preferences
    newsletter_subscribed = models.BooleanField(default=False)
    marketing_emails_enabled = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    @property
    def is_complete(self):
        """Check if the profile has essential information."""
        required_fields = [
            self.phone,
            self.address,
            self.city,
            self.country,
            self.postal_code
        ]
        return all(field for field in required_fields)
    
    def get_full_address(self):
        """Return formatted full address."""
        address_parts = [
            self.address,
            self.city,
            self.postal_code,
            self.country
        ]
        return ', '.join(part for part in address_parts if part)


class Wishlist(models.Model):
    """
    User wishlist model for saving favorite products.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    if TYPE_CHECKING:
        items: 'QuerySet[WishlistItem]'
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    name = models.CharField(max_length=255, default='My Wishlist')
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s {self.name}"
    
    def save(self, *args, **kwargs):
        """Ensure only one default wishlist per user."""
        if self.is_default:
            # Set all other wishlists for this user as non-default
            Wishlist.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def item_count(self) -> int:
        """Get the number of items in this wishlist."""
        return self.items.count()


class WishlistItem(models.Model):
    """
    Items in a user's wishlist.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='wishlist_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ['-added_at']
        unique_together = ['wishlist', 'product', 'variant']
        indexes = [
            models.Index(fields=['wishlist']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.product.name}{variant_info} in {self.wishlist.name}"


# Signal to create user profile automatically
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for User model."""
    if created:
        # Create user profile
        UserProfile.objects.create(user=instance)
        
        # Create default wishlist
        Wishlist.objects.create(
            user=instance,
            name='My Wishlist',
            is_default=True
        )
    else:
        # Save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
