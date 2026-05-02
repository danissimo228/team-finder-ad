# projects/urls.py
from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('create-project/', views.create_project_view, name='create_project'),
    path('<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('<int:project_id>/edit/', views.edit_project_view, name='edit_project'),
    path('list/', views.project_list_view, name='list_projects'),
    path('<int:project_id>/toggle-favorite/', views.toggle_favorite_view, name='toggle_favorite'),
    path('favorites/', views.favorites_view, name='remove_favorite'),
]
