from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    """Custom user model with phone number as primary identifier"""
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    
    # Override username field to make it optional
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.phone_number or self.username or f"User {self.id}"


class UserProfile(models.Model):
    """Extended user profile information"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Subscription tier
    is_pro = models.BooleanField(default=False, help_text="Pro subscriber with access to top 10 analysts")
    pro_expires_at = models.DateTimeField(blank=True, null=True, help_text="When the pro subscription expires")

    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        role_str = "Pro" if self.is_pro_active else "Free"
        return f"{self.user.phone_number} - {role_str}"
        
    @property
    def is_pro_active(self):
        """Check if user has an active pro subscription"""
        from django.utils import timezone
        if self.is_pro and self.pro_expires_at:
            if self.pro_expires_at > timezone.now():
                return True
        return False
    
    @property
    def display_name(self):
        """Return the best display name for the user"""
        if self.user.username:
            return self.user.username
        return self.user.phone_number

    @property
    def user_roles(self):
        """Return list of user's active roles for frontend styling"""
        return ['pro'] if self.is_pro_active else ['free']


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
