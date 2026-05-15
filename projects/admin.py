from django.contrib import admin

from projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    list_display = ("id", "name", "status", "owner", "created_at", "updated_at")
    search_fields = ("name", "description", "owner__username", "owner__email")
