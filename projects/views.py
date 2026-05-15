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


def _paginate(request, queryset, items_per_page=10):
    paginator = Paginator(queryset, items_per_page)
    try:
        page_obj = paginator.page(request.GET.get("page", 1))
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj


@login_required
def toggle_participate(request, project_id):
    if request.method == "POST":
        project = get_object_or_404(Project, id=project_id)
        if project.owner == request.user:
            return JsonResponse(
                {"error": "Владелец проекта не может быть участником"},
                status=HTTPStatus.BAD_REQUEST,
            )

    if project.participants.filter(id=request.user.id).exists():
        project.participants.remove(request.user)
        is_participating = False
    else:
        project.participants.add(request.user)
        is_participating = True

    return JsonResponse(
        {
            "status": HTTPStatus.OK,
            "is_participating": is_participating,
            "participants_count": project.participants.count(),
        },
        status=HTTPStatus.OK,
    )


@login_required
def toggle_favorite(request, project_id):
    if request.method == "POST":
        project = get_object_or_404(Project, id=project_id)
        if project.favorites.filter(id=request.user.id).exists():
            project.favorites.remove(request.user)
            is_favorite = False
        else:
            project.favorites.add(request.user)
            is_favorite = True

        return JsonResponse(
            {"status": HTTPStatus.OK, "is_favorite": is_favorite}, status=HTTPStatus.OK
        )


def create_project_view(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:project_detail", project_id=project.id)
    else:
        form = ProjectForm()

    return render(
        request=request,
        template_name="projects/create-project.html",
        context={
            "form": form,
            "is_edit": False,
        },
    )


def edit_project_view(request, project_id):
    if not request.user.is_authenticated:
        return redirect("users:login")

    project = get_object_or_404(Project, id=project_id)

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

    return render(
        request=request,
        template_name="projects/create-project.html",
        context={
            "form": form,
            "is_edit": True,
            "project": project,
        },
    )


def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(
        request=request,
        template_name="projects/project-details.html",
        context={
            "project": project,
            "is_owner": request.user == project.owner,
            "is_participant": (
                project.participants.filter(id=request.user.id).exists()
                if request.user.is_authenticated
                else False
            ),
        },
    )


def project_list_view(request):
    projects = Project.objects.select_related("owner").all()

    if request.user.is_authenticated:
        projects = projects.annotate(
            is_favorite=Exists(request.user.favorites.filter(id=OuterRef("id")))
        )
    else:
        projects = projects.annotate(
            is_favorite=Value(False, output_field=BooleanField())
        )

    page_obj = _paginate(request, projects, items_per_page=10)
    return render(
        request=request,
        template_name="projects/project_list.html",
        context={
            "projects": page_obj,
            "page_obj": page_obj,
        },
    )


@require_POST
def toggle_favorite_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

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
    if not request.user.is_authenticated:
        return redirect("users:login")

    page_obj = _paginate(request, request.user.favorites.all())
    context = {
        "projects": page_obj,
        "page_obj": page_obj,
        "user": request.user,
    }
    return render(request, "projects/favorite_projects.html", context)
