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

    # User roles - users can have multiple roles
    is_buyer = models.BooleanField(default=True, help_text="Can purchase tips from tipsters")
    is_tipster = models.BooleanField(default=False, help_text="Can share tips and earn revenue")

    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        roles = []
        if self.is_buyer:
            roles.append("Buyer")
        if self.is_tipster:
            roles.append("Tipster")
        role_str = ", ".join(roles) if roles else "No roles"
        return f"{self.user.phone_number} - {role_str}"
    
    @property
    def display_name(self):
        """Return the best display name for the user"""
        if self.user.username:
            return self.user.username
        return self.user.phone_number

    @property
    def user_roles(self):
        """Return list of user's active roles"""
        roles = []
        if self.is_buyer:
            roles.append('buyer')
        if self.is_tipster:
            roles.append('tipster')
        return roles


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
