from django.conf import settings
from django.db import models

# Константы для длин полей
MAX_ABOUT_LENGTH = 500
MAX_PHONE_LENGTH = 20
MAX_GITHUB_URL_LENGTH = 200
AVATAR_UPLOAD_PATH = "avatars/"
DEFAULT_AVATAR_PATH = "/static/images/default-avatar.png"
VERBOSE_NAME_AVATAR = "Аватар"
VERBOSE_NAME_ABOUT = "О себе"
VERBOSE_NAME_PHONE = "Телефон"
VERBOSE_NAME_GITHUB_URL = "GitHub URL"
VERBOSE_NAME_USER_INFO = "Информация о пользователе"
VERBOSE_NAME_USER_INFOS = "Информация о пользователях"


class UserInfo(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="info",
    )
    avatar = models.ImageField(
        upload_to=AVATAR_UPLOAD_PATH,
        null=True,
        blank=True,
        verbose_name=VERBOSE_NAME_AVATAR,
    )
    about = models.TextField(
        max_length=MAX_ABOUT_LENGTH,
        blank=True,
        null=True,
        verbose_name=VERBOSE_NAME_ABOUT,
    )
    phone = models.CharField(
        max_length=MAX_PHONE_LENGTH,
        blank=True,
        null=True,
        verbose_name=VERBOSE_NAME_PHONE,
    )
    github_url = models.URLField(
        max_length=MAX_GITHUB_URL_LENGTH,
        blank=True,
        null=True,
        verbose_name=VERBOSE_NAME_GITHUB_URL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = VERBOSE_NAME_USER_INFO
        verbose_name_plural = VERBOSE_NAME_USER_INFOS

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return DEFAULT_AVATAR_PATH
