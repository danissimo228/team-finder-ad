"""
Настройка URL-адреса для приложения пользователей.
"""

from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Управление профилем
    path("<int:user_id>/", views.user_profile_view, name="user_profile"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    # Список участников
    path("list/", views.participants_list_view, name="participants_list"),
]
