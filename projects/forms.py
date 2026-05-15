from django import forms

from projects.models import Project

MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 200
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 5000
DESCRIPTION_ROWS = 6
GITHUB_URL_PREFIX = "https://github.com/"
GITHUB_URL_PLACEHOLDER = "https://github.com/username/project"
NAME_PLACEHOLDER = "Введите название проекта"
DESCRIPTION_PLACEHOLDER = "Опишите ваш проект..."
ERROR_NAME_TOO_SHORT = (
    f"Название проекта должно содержать минимум {MIN_NAME_LENGTH} символа"
)
ERROR_NAME_TOO_LONG = f"Название проекта не должно превышать {MAX_NAME_LENGTH} символов"
ERROR_DESCRIPTION_TOO_SHORT = (
    f"Описание должно содержать минимум {MIN_DESCRIPTION_LENGTH} символов"
)
ERROR_DESCRIPTION_TOO_LONG = (
    f"Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов"
)
ERROR_INVALID_GITHUB_URL = "Введите корректную ссылку на GitHub репозиторий"


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": NAME_PLACEHOLDER,
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": DESCRIPTION_PLACEHOLDER,
                    "rows": DESCRIPTION_ROWS,
                    "class": "form-control",
                }
            ),
            "github_url": forms.URLInput(
                attrs={
                    "placeholder": GITHUB_URL_PLACEHOLDER,
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
        if len(name) < MIN_NAME_LENGTH:
            raise forms.ValidationError(ERROR_NAME_TOO_SHORT)
        if len(name) > MAX_NAME_LENGTH:
            raise forms.ValidationError(ERROR_NAME_TOO_LONG)
        return name

    def clean_description(self):
        description = self.cleaned_data.get("description")
        if len(description) < MIN_DESCRIPTION_LENGTH:
            raise forms.ValidationError(ERROR_DESCRIPTION_TOO_SHORT)
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise forms.ValidationError(ERROR_DESCRIPTION_TOO_LONG)
        return description

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and not url.startswith(GITHUB_URL_PREFIX):
            raise forms.ValidationError(ERROR_INVALID_GITHUB_URL)
        return url
