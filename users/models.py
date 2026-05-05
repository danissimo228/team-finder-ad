# models.py
from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="Аватар"
    )
    about = models.TextField(
        max_length=500, blank=True, null=True, verbose_name="О себе"
    )
    phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Телефон"
    )
    github_url = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="GitHub URL"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username}"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "/static/images/default-avatar.png"
