# projects/forms.py
from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Введите название проекта",
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Опишите ваш проект...",
                    "rows": 6,
                    "class": "form-control",
                }
            ),
            "github_url": forms.URLInput(
                attrs={
                    "placeholder": "https://github.com/username/project",
                    "class": "form-control",
                }
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Название проекта",
            "description": "Описание",
            "github_url": "GitHub ссылка",
            "status": "Статус проекта",
        }
        help_texts = {
            "github_url": "Введите полную ссылку на GitHub репозиторий",
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if len(name) < 3:
            raise forms.ValidationError(
                "Название проекта должно содержать минимум 3 символа"
            )
        if len(name) > 200:
            raise forms.ValidationError(
                "Название проекта не должно превышать 200 символов"
            )
        return name

    def clean_description(self):
        description = self.cleaned_data.get("description")
        if len(description) < 10:
            raise forms.ValidationError("Описание должно содержать минимум 10 символов")
        if len(description) > 5000:
            raise forms.ValidationError("Описание не должно превышать 5000 символов")
        return description

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and not url.startswith("https://github.com/"):
            raise forms.ValidationError(
                "Введите корректную ссылку на GitHub репозиторий"
            )
        return url
