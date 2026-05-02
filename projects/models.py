# projects/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Project(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('closed', 'Закрыт'),
        ('in_progress', 'В разработке'),
        ('completed', 'Завершен'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название проекта')
    description = models.TextField(verbose_name='Описание проекта')
    github_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='GitHub ссылка')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name='Статус')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects', verbose_name='Владелец')
    participants = models.ManyToManyField(User, related_name='participating_projects', blank=True, verbose_name='Участники')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    favorites = models.ManyToManyField(
        User, 
        related_name='favorite_projects',  # Это создаст атрибут favorite_projects у User
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'project_id': self.id})
