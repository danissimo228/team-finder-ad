# admin.py
from django.contrib import admin
from users.models import UserInfo


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone", "github_url", "created_at")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
