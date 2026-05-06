# projects/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.forms import ProjectForm
from projects.models import Project


@login_required
def toggle_participate(request, project_id):
    """
    Добавляет или удаляет текущего пользователя из участников проекта.
    URL: /projects/<int:project_id>/toggle-participate/
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    project = get_object_or_404(Project, id=project_id)

    # Владелец проекта не может быть участником
    if project.owner == request.user:
        return JsonResponse(
            {"error": "Project owner cannot participate in own project"}, status=400
        )

    # Переключаем статус участия
    if request.user in project.participants.all():
        project.participants.remove(request.user)
        is_participating = False
    else:
        project.participants.add(request.user)
        is_participating = True

    return JsonResponse(
        {
            "status": "ok",
            "is_participating": is_participating,
            "participants_count": project.participants.count(),
        }
    )


@login_required
def toggle_favorite(request, project_id):
    """
    Добавляет или удаляет проект из избранного текущего пользователя.
    URL: /projects/<int:project_id>/toggle-favorite/
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    project = get_object_or_404(Project, id=project_id)

    if project.favorites.filter(id=request.user.id).exists():
        project.favorites.remove(request.user)
        is_favorite = False
    else:
        project.favorites.add(request.user)
        is_favorite = True

    return JsonResponse({"status": "ok", "is_favorite": is_favorite})


def create_project_view(request):
    """Создание нового проекта"""
    if not request.user.is_authenticated:
        return redirect("users:login")

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
    return render(request, "projects/create-project.html", context)


def edit_project_view(request, project_id):
    """Редактирование проекта"""
    if not request.user.is_authenticated:
        return redirect("users:login")

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
    return render(request, "projects/create-project.html", context)


def project_detail_view(request, project_id):
    """Просмотр деталей проекта"""
    project = get_object_or_404(Project, id=project_id)

    is_participant = False
    if request.user.is_authenticated:
        is_participant = project.participants.filter(id=request.user.id).exists()

    context = {
        "project": project,
        "is_owner": request.user == project.owner,
        "is_participant": is_participant,
    }
    return render(request, "projects/project-details.html", context)


def project_list_view(request):
    projects = Project.objects.select_related("owner").all()
    if request.user.is_authenticated:
        favorites = request.user.favorites.filter(id=OuterRef("id"))
        projects = projects.annotate(is_favorite=Exists(favorites))
    else:
        projects = projects.annotate(
            is_favorite=Value(False, output_field=BooleanField())
        )

    # 10 проектов на страницу, можно 6 как в комментарии
    paginator = Paginator(projects, 10)
    page = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "projects": page_obj,
        "page_obj": page_obj,
    }
    return render(request, "projects/project_list.html", context)


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
    """Страница избранных проектов пользователя"""
    if not request.user.is_authenticated:
        return redirect("users:login")

    # Получаем избранные проекты
    projects = request.user.favorites.all()
    context = {"projects": projects, "user": request.user}
    return render(request, "projects/favorite_projects.html", context)
