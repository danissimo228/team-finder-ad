# projects/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project
from .forms import ProjectForm


def create_project_view(request):
    """Создание нового проекта"""
    if not request.user.is_authenticated:
        return redirect("/users/login")

    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            # Добавляем владельца как участника проекта
            project.participants.add(request.user)
            messages.success(request, f'Проект "{project.name}" успешно создан!')
            return redirect("projects:project_detail", project_id=project.id)
    else:
        form = ProjectForm()

    context = {
        "form": form,
        "is_edit": False,
    }
    return render(request, "../templates_var1/projects/create-project.html", context)


def edit_project_view(request, project_id):
    """Редактирование проекта"""
    if not request.user.is_authenticated:
        return redirect("/users/login")

    project = get_object_or_404(Project, id=project_id)

    # Проверяем, является ли пользователь владельцем
    if project.owner != request.user:
        messages.error(request, "У вас нет прав для редактирования этого проекта")
        return redirect("projects:project_detail", project_id=project.id)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Проект "{project.name}" успешно обновлен!')
            return redirect("projects:project_detail", project_id=project.id)
    else:
        form = ProjectForm(instance=project)

    context = {
        "form": form,
        "is_edit": True,
        "project": project,
    }
    return render(request, "../templates_var1/projects/create-project.html", context)


def project_detail_view(request, project_id):
    """Просмотр деталей проекта"""
    project = get_object_or_404(Project, id=project_id)

    context = {
        "project": project,
        "is_owner": request.user == project.owner,
        "is_participant": (
            request.user in project.participants.all()
            if request.user.is_authenticated
            else False
        ),
    }
    return render(request, "../templates_var1/projects/project-details.html", context)


def project_list_view(request):
    """Просмотр всех актуальных проектов"""
    # Получаем все проекты
    projects = Project.objects.all().order_by("-created_at")

    # Для авторизованных пользователей добавляем предзагрузку избранного
    if request.user.is_authenticated:
        # Загружаем проекты с аннотацией о избранном
        favorite_project_ids = request.user.favorites.values_list("id", flat=True)

        for project in projects:
            # Добавляем атрибут для проверки в шаблоне
            project.is_favorite = project.id in favorite_project_ids

    context = {
        "projects": projects,
    }
    return render(request, "../templates_var1/projects/project_list.html", context)


from django.views.decorators.http import require_POST


@require_POST
def toggle_favorite_view(request, project_id):
    """Добавление/удаление проекта из избранного (AJAX)"""
    project = get_object_or_404(Project, id=project_id)

    # Добавляем или удаляем из избранного
    if project.favorites.filter(id=request.user.id).exists():
        project.favorites.remove(request.user)
        is_favorite = False
        message = "Удалено из избранного"
    else:
        project.favorites.add(request.user)
        is_favorite = True
        message = "Добавлено в избранное"

    return JsonResponse(
        {
            "is_favorite": is_favorite,
            "message": message,
            "favorites_count": project.favorites.count(),
        }
    )


@login_required
def favorites_view(request):
    """
    Страница избранных проектов пользователя
    """
    if not request.user.is_authenticated:
        return redirect("/users/login")

    # Получаем избранные проекты
    projects = request.user.favorites.all().order_by("-created_at")
    context = {"projects": projects, "user": request.user}
    return render(request, "../templates_var1/projects/favorite_projects.html", context)
