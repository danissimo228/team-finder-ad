# projects/models.py
from django.contrib.auth.models import User
from django.db import models


STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"

STATUS_CHOICES = [
    (STATUS_OPEN, "Открыт"),
    (STATUS_CLOSED, "Закрыт"),
    (STATUS_IN_PROGRESS, "В разработке"),
    (STATUS_COMPLETED, "Завершен"),
]


MAX_NAME_LENGTH = 200
MAX_GITHUB_URL_LENGTH = 500
MAX_STATUS_LENGTH = 20


class Project(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name="Название проекта")
    description = models.TextField(verbose_name="Описание проекта")
    github_url = models.URLField(
        max_length=MAX_GITHUB_URL_LENGTH,
        blank=True,
        null=True,
        verbose_name="GitHub ссылка",
    )
    status = models.CharField(
        max_length=MAX_STATUS_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        verbose_name="Статус",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Владелец",
    )
    participants = models.ManyToManyField(
        User,
        related_name="participating_projects",
        blank=True,
        verbose_name="Участники",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    favorites = models.ManyToManyField(
        User,
        related_name="favorites",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
