"""
Представления для управления пользователями, включая регистрацию, аутентификацию, управление профилями,
и список пользователей с расширенной фильтрацией.
"""

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project
from users.models import UserProfile

from .forms import LoginForm, RegistrationForm, UpdateUserProfileForm, UserProfileDTO

# Константы для фильтров
FILTER_OWNERS_OF_FAVORITE_PROJECTS = "owners-of-favorite-projects"
FILTER_OWNERS_OF_PARTICIPATING_PROJECTS = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY_PROJECTS = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"

# Константы для пагинации
USERS_PER_PAGE = 12

# Константы для сообщений
MESSAGE_PROFILE_UPDATED = "Профиль успешно обновлен!"
MESSAGE_PASSWORD_CHANGED = "Ваш пароль был успешно изменен!"


def paginate_queryset(request, queryset, items_per_page=USERS_PER_PAGE):
    """
    Универсальная функция для пагинации queryset.

    Args:
        request: HTTP request object
        queryset: QuerySet для пагинации
        items_per_page: Количество элементов на странице

    Returns:
        Page object: Объект страницы с элементами
    """
    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def register_view(request):
    """
    Регистрация нового пользователя.

    URL: /users/register/

    GET: Отображает форму регистрации.
    POST: Обрабатывает данные формы, создает нового пользователя и выполняет вход.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Страница регистрации или редирект на список проектов
    """
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Создаем пользователя через метод формы
            user = form.save(request)

            # Выполняем вход для созданного пользователя
            login(request, user)
            return redirect("projects:list_projects")
    else:
        form = RegistrationForm()

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """
    Авторизация пользователя.

    URL: /users/login/

    GET: Отображает форму входа.
    POST: Проверяет учетные данные и выполняет вход пользователя.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Страница входа или редирект на список проектов
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            return redirect("projects:list_projects")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    """
    Выход пользователя из системы.

    URL: /users/logout/

    Выполняет выход пользователя и перенаправляет на страницу входа.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Редирект на страницу входа
    """
    logout(request)
    return redirect("users:login")


def user_profile_view(request, user_id):
    """
    Просмотр профиля пользователя.

    URL: /users/<int:user_id>/

    Args:
        request: HTTP request object
        user_id: ID пользователя, профиль которого просматривается

    Returns:
        HttpResponse: Страница профиля пользователя
    """
    user = get_object_or_404(User, id=user_id, is_active=True)
    owned_projects = user.owned_projects.all()

    # Создаём DTO вместо динамического добавления атрибутов
    user_dto = UserProfileDTO(user)

    context = {
        "user": user_dto,
        "request": request,
        "owned_projects": owned_projects,
    }

    return render(request, "users/user-details.html", context)


def edit_profile(request):
    """
    Редактирование профиля текущего пользователя.

    URL: /users/edit-profile/

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Страница редактирования профиля или редирект на профиль
    """
    if not request.user.is_authenticated:
        return redirect("users:login")

    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UpdateUserProfileForm(
            request.POST,
            request.FILES,
            instance=user_profile,
            user_instance=request.user,
        )

        if form.is_valid():
            form.save()
            messages.success(request, MESSAGE_PROFILE_UPDATED)
            return redirect("users:user_profile", user_id=request.user.id)
    else:
        form = UpdateUserProfileForm(instance=user_profile, user_instance=request.user)

    context = {
        "form": form,
        "user": request.user,
    }

    return render(request, "users/edit_profile.html", context)


def change_password(request):
    """
    Смена пароля пользователя.

    URL: /users/change-password/

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Страница смены пароля или редирект на профиль
    """
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)

        if form.is_valid():
            user = form.save()
            # Обновляем сессию, чтобы пользователь не вышел
            update_session_auth_hash(request, user)
            messages.success(request, MESSAGE_PASSWORD_CHANGED)
            return redirect("users:user_profile", user_id=request.user.id)
    else:
        form = PasswordChangeForm(user=request.user)

    context = {
        "form": form,
    }
    return render(request, "users/change_password.html", context)


def participants_list_view(request):
    """
    Список участников платформы с фильтрацией.
    """
    # Базовый запрос - исключаем текущего пользователя и подгружаем профили
    if request.user.is_authenticated:
        users = User.objects.exclude(id=request.user.id)
    else:
        users = User.objects.all()

    active_filter = request.GET.get("filter", "")

    # Применяем фильтры для авторизованных пользователей
    if request.user.is_authenticated and active_filter:
        if active_filter == FILTER_OWNERS_OF_FAVORITE_PROJECTS:
            users = users.filter(
                owned_projects__in=request.user.favorites.all()
            ).distinct()

        elif active_filter == FILTER_OWNERS_OF_PARTICIPATING_PROJECTS:
            users = users.filter(
                owned_projects__in=request.user.participating_projects.all()
            ).distinct()

        elif active_filter == FILTER_INTERESTED_IN_MY_PROJECTS:
            users = users.filter(
                favorites__in=Project.objects.filter(owner=request.user)
            ).distinct()

        elif active_filter == FILTER_PARTICIPANTS_OF_MY_PROJECTS:
            users = users.filter(
                participating_projects__in=Project.objects.filter(owner=request.user)
            ).distinct()

    # Аннотируем дополнительной информацией и подгружаем профили одним запросом
    users = users.select_related("profile").annotate(
        projects_count=Count("owned_projects", distinct=True),
        participating_count=Count("participating_projects", distinct=True),
        favorites_count=Count("favorites", distinct=True),
    )

    # Сортировка
    users = users.order_by("first_name", "last_name")

    # Пагинация
    participants_page = paginate_queryset(request, users, USERS_PER_PAGE)

    # Создаём список DTO вместо динамического добавления атрибутов
    participants_list = [UserProfileDTO(user) for user in participants_page]

    context = {
        "participants": participants_list,
        "active_filter": active_filter,
    }

    return render(request, "users/participants.html", context)
