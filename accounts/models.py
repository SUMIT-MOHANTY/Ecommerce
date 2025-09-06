from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True, help_text="Digits only, 7-15 characters")

    def __str__(self):
        return f"Profile({self.user.username})"
