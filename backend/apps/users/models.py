"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, sub, **extra_fields):
        user = self.model(sub=sub, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, sub, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(sub, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    sub = models.CharField(max_length=255, primary_key=True)
    email = models.EmailField(blank=True)
    given_name = models.CharField(max_length=150, blank=True)
    family_name = models.CharField(max_length=150, blank=True)
    picture = models.URLField(blank=True)
    nickname = models.CharField(max_length=120, blank=True, default="")
    avatar_visible = models.BooleanField(default=True)
    theme_config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "sub"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.password:
            self.set_unusable_password()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sub


class AccessRequest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} -> {self.role}"
