from django.contrib import admin

from projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "owner", "created_at", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("name", "description", "owner__username", "owner__email")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
    list_editable = ("status",)

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("name", "description", "github_url", "status")},
        ),
        (
            "Участники",
            {"fields": ("owner", "participants", "favorites")},
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),  # Сворачиваемый блок
            },
        ),
    )
