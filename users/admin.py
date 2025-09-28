from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile, Wishlist, WishlistItem

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = ('user', 'phone', 'city', 'country', 'is_complete', 'created_at')
    list_filter = ('newsletter_subscribed', 'marketing_emails_enabled', 'country', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone', 'city')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Contact Information', {'fields': ('phone',)}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Profile', {'fields': ('date_of_birth', 'bio', 'avatar')}),
        ('Preferences', {'fields': ('newsletter_subscribed', 'marketing_emails_enabled')}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


class WishlistItemInline(admin.TabularInline):
    """
    Inline admin for WishlistItem.
    """
    model = WishlistItem
    extra = 0
    readonly_fields = ('added_at',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """
    Admin configuration for Wishlist model.
    """
    list_display = ('user', 'name', 'is_default', 'is_public', 'item_count', 'created_at')
    list_filter = ('is_default', 'is_public', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [WishlistItemInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('user', 'name')}),
        ('Settings', {'fields': ('is_default', 'is_public')}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for WishlistItem model.
    """
    list_display = ('wishlist', 'product', 'variant', 'added_at')
    list_filter = ('added_at', 'wishlist__user')
    search_fields = ('wishlist__name', 'product__name', 'variant__name')
    readonly_fields = ('id', 'added_at')
    
    fieldsets = (
        ('Item Details', {'fields': ('wishlist', 'product', 'variant')}),
        ('Metadata', {'fields': ('id', 'added_at')}),
    )
