# projects/views.py
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.forms import ProjectForm
from projects.models import Project


def paginate_queryset(request, queryset, items_per_page=10):
    """
    Универсальная функция для пагинации queryset.

    Args:
        request: HTTP request объект
        queryset: QuerySet для пагинации
        items_per_page: количество элементов на странице

    Returns:
        page_obj: объект страницы
    """
    paginator = Paginator(queryset, items_per_page)
    page = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj


@login_required
def toggle_participate(request, project_id):
    """
    Добавляет или удаляет текущего пользователя из участников проекта.
    URL: /projects/<int:project_id>/toggle-participate/
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"}, status=HTTPStatus.METHOD_NOT_ALLOWED
        )

    project = get_object_or_404(Project, id=project_id)

    # Владелец проекта не может быть участником
    if project.owner == request.user:
        return JsonResponse(
            {"error": "Project owner cannot participate in own project"},
            status=HTTPStatus.BAD_REQUEST,
        )

    # Переключаем статус участия (оптимизированная версия)
    is_participant = project.participants.filter(id=request.user.id).exists()

    if is_participant:
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
        },
        status=HTTPStatus.OK,
    )


@login_required
def toggle_favorite(request, project_id):
    """
    Добавляет или удаляет проект из избранного текущего пользователя.
    URL: /projects/<int:project_id>/toggle-favorite/
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"}, status=HTTPStatus.METHOD_NOT_ALLOWED
        )

    project = get_object_or_404(Project, id=project_id)

    if project.favorites.filter(id=request.user.id).exists():
        project.favorites.remove(request.user)
        is_favorite = False
    else:
        project.favorites.add(request.user)
        is_favorite = True

    return JsonResponse(
        {"status": "ok", "is_favorite": is_favorite}, status=HTTPStatus.OK
    )


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
    """Список проектов с пагинацией"""
    projects = Project.objects.select_related("owner").all()

    if request.user.is_authenticated:
        favorites = request.user.favorites.filter(id=OuterRef("id"))
        projects = projects.annotate(is_favorite=Exists(favorites))
    else:
        projects = projects.annotate(
            is_favorite=Value(False, output_field=BooleanField())
        )

    # Используем функцию пагинации
    page_obj = paginate_queryset(request, projects, items_per_page=10)

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
        },
        status=HTTPStatus.OK,
    )


@login_required
def favorites_view(request):
    """Страница избранных проектов пользователя с пагинацией"""
    if not request.user.is_authenticated:
        return redirect("users:login")

    # Получаем избранные проекты
    favorites_queryset = request.user.favorites.all()

    # Добавляем пагинацию для избранных проектов (например, 6 на страницу)
    page_obj = paginate_queryset(request, favorites_queryset, items_per_page=6)

    context = {
        "projects": page_obj,
        "page_obj": page_obj,
        "user": request.user,
    }
    return render(request, "projects/favorite_projects.html", context)
