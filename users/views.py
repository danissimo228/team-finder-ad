from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project
from users.models import UserInfo

from users.forms import LoginForm, RegistrationForm, UpdateUserInfoForm, FullUser

USERS_PER_PAGE = 10

FILTER_OWNERS_OF_FAVORITE_PROJECTS = "owners-of-favorite-projects"
FILTER_OWNERS_OF_PARTICIPATING_PROJECTS = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY_PROJECTS = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"

MESSAGE_PROFILE_UPDATED = "Профиль успешно обновлен!"
MESSAGE_PASSWORD_CHANGED = "Ваш пароль был успешно изменен!"


def _paginate(request, queryset, items_per_page=USERS_PER_PAGE):
    paginator = Paginator(queryset, items_per_page)
    return paginator.get_page(request.GET.get("page"))


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            login(request, user)
            return redirect("projects:list_projects")
    else:
        form = RegistrationForm()

    return render(
        request=request, template_name="users/register.html", context={"form": form}
    )


def login_view(request):
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
    logout(request)
    return redirect("users:login")


def user_profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id, is_active=True)
    return render(
        request=request,
        template_name="users/user-details.html",
        context={
            "user": FullUser(user),
            "request": request,
            "owned_projects": user.owned_projects.all(),
        },
    )


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    user_profile, _ = UserInfo.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UpdateUserInfoForm(
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
        form = UpdateUserInfoForm(instance=user_profile, user_instance=request.user)

    return render(
        request=request,
        template_name="users/edit_profile.html",
        context={
            "form": form,
            "user": request.user,
        },
    )


def change_password(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, MESSAGE_PASSWORD_CHANGED)
            return redirect("users:user_profile", user_id=request.user.id)
    else:
        form = PasswordChangeForm(user=request.user)

    return render(
        request=request,
        template_name="users/change_password.html",
        context={
            "form": form,
        },
    )


def participants_list_view(request):
    users = (
        User.objects.exclude(id=request.user.id)
        if request.user.is_authenticated
        else User.objects.all()
    )

    active_filter = request.GET.get("filter", "")

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

    users = (
        users.select_related("info")
        .annotate(
            projects_count=Count("owned_projects", distinct=True),
            participating_count=Count("participating_projects", distinct=True),
            favorites_count=Count("favorites", distinct=True),
        )
        .order_by("first_name", "last_name")
    )

    return render(
        request=request,
        template_name="users/participants.html",
        context={
            "active_filter": active_filter,
            "participants": [
                FullUser(user) for user in _paginate(request, users, USERS_PER_PAGE)
            ],
        },
    )
