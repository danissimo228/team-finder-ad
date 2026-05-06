from django.contrib import admin
from django.utils.html import format_html

from users.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone", "github_url", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "user__email", "phone", "about")
    readonly_fields = ("created_at", "updated_at", "get_avatar_preview")
    list_select_related = ("user",)

    fieldsets = (
        ("Пользователь", {"fields": ("user",)}),
        (
            "Личная информация",
            {
                "fields": (
                    "avatar",
                    "get_avatar_preview",
                    "about",
                    "phone",
                    "github_url",
                )
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.avatar.url,
            )
        return "Нет аватара"

    get_avatar_preview.short_description = "Превью аватара"
