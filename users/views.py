"""
Представления для управления пользователями, включая регистрацию, аутентификацию, управление профилями,
и список пользователей с расширенной фильтрацией.
"""

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator

from projects.models import Project
from users.models import UserProfile
from .forms import RegistrationForm, LoginForm, UpdateUserProfileForm
from django.contrib.auth.forms import PasswordChangeForm


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
    if request.user.is_authenticated:
        return redirect("/projects/list/")
    
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            surname = form.cleaned_data["surname"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            
            # Генерируем username из email
            username = email.split("@")[0]
            if User.objects.filter(username=username).exists():
                username = f"{username}_{User.objects.count()}"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name,
                last_name=surname
            )
            
            login(request, user)
            return redirect("/projects/list/")
    else:
        form = RegistrationForm()
    
    return render(request, "../templates_var1/users/register.html", {"form": form})


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
    if request.user.is_authenticated:
        return redirect("/projects/list/")
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            return redirect("/projects/list/")
    else:
        form = LoginForm()
    
    return render(request, "../templates_var1/users/login.html", {"form": form})


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
    return redirect("/users/login")


@login_required
def user_profile_view(request, user_id):
    """
    Просмотр профиля пользователя.
    
    URL: /users/<int:user_id>/
    
    Отображает детальную информацию о пользователе:
    - Проекты пользователя
    - Участие в проектах
    - Избранные проекты
    - Статистику
    - Общие проекты с текущим пользователем
    
    Args:
        request: HTTP request object
        user_id: ID пользователя, профиль которого просматривается
        
    Returns:
        HttpResponse: Страница профиля пользователя
    """
    user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Получаем проекты пользователя
    owned_projects = user.owned_projects.all().order_by("-created_at")
    participating_projects = user.participating_projects.all().order_by("-created_at")
    favorite_projects = user.favorite_projects.all().order_by("-created_at")
    
    # Статистика пользователя
    stats = {
        "projects_count": owned_projects.count(),
        "participating_count": participating_projects.count(),
        "favorites_count": favorite_projects.count(),
    }
    
    # Общие проекты с текущим пользователем
    common_projects = []
    is_following = False
    
    if request.user.is_authenticated and request.user != user:
        common_projects = Project.objects.filter(
            participants=request.user
        ).filter(
            participants=user
        ).distinct()
    
    context = {
        "profile_user": user,
        "owned_projects": owned_projects,
        "participating_projects": participating_projects,
        "favorite_projects": favorite_projects,
        "stats": stats,
        "common_projects": common_projects,
        "is_following": is_following,
    }
    
    return render(request, "../templates_var1/users/user-details.html", context)


@login_required
def edit_profile(request):
    """
    Редактирование профиля текущего пользователя.
    
    URL: /users/edit-profile/
    
    GET: Отображает форму редактирования профиля.
    POST: Сохраняет изменения в профиле и модели User.
    
    Обновляет:
    - Аватар
    - Информацию о себе
    - Телефон
    - GitHub URL
    - Имя и фамилию (в модели User)
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Страница редактирования профиля или редирект на профиль
    """
    user_profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )
    
    if request.method == "POST":
        form = UpdateUserProfileForm(
            request.POST,
            request.FILES,
            instance=user_profile,
            user_instance=request.user
        )
        
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен!")
            return redirect("users:user_profile", user_id=request.user.id)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = UpdateUserProfileForm(
            instance=user_profile,
            user_instance=request.user
        )
    
    context = {
        "form": form,
        "user": request.user,
    }
    
    return render(request, "../templates_var1/users/edit_profile.html", context)


@login_required
def change_password(request):
    """
    Смена пароля пользователя.
    
    URL: /users/change-password/
    
    GET: Отображает форму смены пароля.
    POST: Проверяет и сохраняет новый пароль, обновляет сессию.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Страница смены пароля или редирект на профиль
    """
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            user = form.save()
            # Обновляем сессию, чтобы пользователь не вышел
            update_session_auth_hash(request, user)
            messages.success(request, "Ваш пароль был успешно изменен!")
            return redirect("users:user_profile", user_id=request.user.id)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = PasswordChangeForm(user=request.user)
    
    context = {
        "form": form,
    }
    return render(request, "../templates_var1/users/change_password.html", context)


def participants_list_view(request):
    """
    Список участников платформы с фильтрацией.
    
    URL: /users/list/
    
    Поддерживаемые фильтры (для авторизованных пользователей):
    - owners-of-favorite-projects: Авторы проектов, добавленных в избранное
    - owners-of-participating-projects: Авторы проектов, в которых участвует пользователь
    - interested-in-my-projects: Пользователи, добавившие в избранное проекты текущего пользователя
    - participants-of-my-projects: Участники проектов текущего пользователя
    
    Args:
        request: HTTP request object
        
    Query Parameters:
        filter: Тип фильтрации (str, optional)
        page: Номер страницы для пагинации (int, optional)
        
    Returns:
        HttpResponse: Страница со списком участников
    """
    # Базовый запрос - исключаем текущего пользователя
    if request.user.is_authenticated:
        users = User.objects.exclude(id=request.user.id)
    else:
        users = User.objects.all()
    
    # Получаем параметр фильтра
    active_filter = request.GET.get("filter", "")
    
    # Применяем фильтры для авторизованных пользователей
    if request.user.is_authenticated and active_filter:
        if active_filter == "owners-of-favorite-projects":
            # Авторы избранных проектов
            favorite_projects_ids = request.user.favorite_projects.values_list("id", flat=True)
            users = users.filter(
                owned_projects__id__in=favorite_projects_ids
            ).distinct()
            
        elif active_filter == "owners-of-participating-projects":
            # Авторы проектов, в которых я участвую
            participating_projects_ids = request.user.participating_projects.values_list("id", flat=True)
            users = users.filter(
                owned_projects__id__in=participating_projects_ids
            ).distinct()
            
        elif active_filter == "interested-in-my-projects":
            # Пользователи, которым нравятся мои проекты
            my_projects_ids = Project.objects.filter(
                owner=request.user
            ).values_list("id", flat=True)
            
            users = users.filter(
                favorite_projects__id__in=my_projects_ids
            ).distinct()
            
        elif active_filter == "participants-of-my-projects":
            # Участники моих проектов
            my_projects_ids = Project.objects.filter(
                owner=request.user
            ).values_list("id", flat=True)
            
            users = users.filter(
                participating_projects__id__in=my_projects_ids
            ).distinct()
    
    # Аннотируем дополнительной информацией
    users = users.annotate(
        projects_count=Count("owned_projects", distinct=True),
        participating_count=Count("participating_projects", distinct=True),
        favorites_count=Count("favorite_projects", distinct=True)
    )
    
    # Сортировка
    users = users.order_by("first_name", "last_name")
    
    # Пагинация
    paginator = Paginator(users, 12)
    page_number = request.GET.get("page")
    participants = paginator.get_page(page_number)
    
    # Добавляем атрибуты для совместимости с шаблоном
    for user in participants:
        user.name = user.first_name or user.username
        user.surname = user.last_name or ""
        user.avatar = None  # Будет заменено при наличии UserProfile
        user.about = ""
        
        # Если есть профиль, подгружаем аватар и about
        if hasattr(user, "profile") and user.profile:
            user.avatar = user.profile.avatar
            user.about = user.profile.about
    
    context = {
        "participants": participants,
        "active_filter": active_filter,
        "paginator": paginator,
    }
    
    return render(request, "../templates_var1/users/participants.html", context)