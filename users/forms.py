"""
Формы для управления пользователями, включая регистрацию, аутентификацию и редактирование профиля.
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.validators import RegexValidator

from users.models import UserProfile


class RegistrationForm(forms.Form):
    """
    Форма регистрации нового пользователя.

    URL: /users/register/

    Поля:
        name: Имя пользователя (только буквы)
        surname: Фамилия пользователя (только буквы)
        email: Email адрес (должен быть уникальным)
        password: Пароль (минимум 6 символов)
    """

    name = forms.CharField(
        max_length=30,
        label="Имя",
        widget=forms.TextInput(attrs={"placeholder": "Введите имя"}),
    )
    surname = forms.CharField(
        max_length=30,
        label="Фамилия",
        widget=forms.TextInput(attrs={"placeholder": "Введите фамилию"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "example@mail.com"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
    )

    def clean_email(self):
        """
        Проверяет, что email не используется другим пользователем.

        Returns:
            str: Очищенный email

        Raises:
            forms.ValidationError: Если email уже существует
        """
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

    def clean_name(self):
        """
        Проверяет, что имя содержит только буквы.

        Returns:
            str: Очищенное имя

        Raises:
            forms.ValidationError: Если имя содержит небуквенные символы
        """
        name = self.cleaned_data.get("name")
        if not name.isalpha():
            raise forms.ValidationError("Имя должно содержать только буквы")
        return name

    def clean_surname(self):
        """
        Проверяет, что фамилия содержит только буквы.

        Returns:
            str: Очищенная фамилия

        Raises:
            forms.ValidationError: Если фамилия содержит небуквенные символы
        """
        surname = self.cleaned_data.get("surname")
        if not surname.isalpha():
            raise forms.ValidationError("Фамилия должна содержать только буквы")
        return surname

    def clean_password(self):
        """
        Проверяет, что пароль соответствует требованиям безопасности.

        Returns:
            str: Очищенный пароль

        Raises:
            forms.ValidationError: Если пароль слишком короткий
        """
        password = self.cleaned_data.get("password")
        if len(password) < 6:
            raise forms.ValidationError("Пароль должен содержать минимум 6 символов")
        return password


class LoginForm(forms.Form):
    """
    Форма авторизации пользователя.

    URL: /users/login/

    Поля:
        email: Email пользователя
        password: Пароль пользователя
    """

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"placeholder": "example@mail.com", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
    )

    def clean(self):
        """
        Проверяет учетные данные пользователя.

        Аутентифицирует пользователя по email и паролю.

        Returns:
            dict: Очищенные данные с добавленным объектом user

        Raises:
            forms.ValidationError: Если email не найден или пароль неверный
        """
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
                if user is None:
                    raise forms.ValidationError("Неверный email или пароль")
                if not user.is_active:
                    raise forms.ValidationError("Учетная запись не активирована")
                cleaned_data["user"] = user
            except User.DoesNotExist:
                raise forms.ValidationError("Пользователь с таким email не найден")

        return cleaned_data


class ChangePasswordForm(forms.Form):
    """
    Форма смены пароля.

    URL: /users/change-password/

    Поля:
        old_password: Текущий пароль
        new_password1: Новый пароль
        new_password2: Подтверждение нового пароля
    """

    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите текущий пароль"}),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите новый пароль"}),
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={"placeholder": "Подтвердите новый пароль"}),
    )

    def __init__(self, user, *args, **kwargs):
        """
        Инициализирует форму с объектом пользователя.

        Args:
            user: Объект User для которого меняется пароль
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        """
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """
        Проверяет правильность текущего пароля.

        Returns:
            str: Текущий пароль

        Raises:
            forms.ValidationError: Если пароль неверный
        """
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Неверный текущий пароль")
        return old_password

    def clean_new_password2(self):
        """
        Проверяет совпадение нового пароля и его подтверждения,
        а также валидность пароля.

        Returns:
            str: Подтверждение нового пароля

        Raises:
            forms.ValidationError: Если пароли не совпадают или пароль невалидный
        """
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Пароли не совпадают")

        # Валидация пароля с помощью встроенных валидаторов Django
        if new_password1:
            try:
                password_validation.validate_password(new_password1, self.user)
            except forms.ValidationError as e:
                self.add_error("new_password1", e)

        return new_password2

    def save(self, commit=True):
        """
        Сохраняет новый пароль для пользователя.

        Args:
            commit: Сохранять ли изменения в БД

        Returns:
            User: Объект пользователя с обновленным паролем
        """
        new_password = self.cleaned_data.get("new_password1")
        self.user.set_password(new_password)
        if commit:
            self.user.save()
        return self.user


class UserProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя (устаревшая).

    URL: /users/edit-profile/

    Поля:
        name: Имя пользователя
        surname: Фамилия пользователя
        about: Информация о себе
        email: Email адрес
        phone: Номер телефона
        github_url: Ссылка на GitHub
        avatar: Аватар пользователя

    Note:
        Эта форма устарела. Используйте UpdateUserProfileForm.
    """

    name = forms.CharField(
        max_length=30,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    surname = forms.CharField(
        max_length=30,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    about = forms.CharField(
        required=False,
        label="О себе",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Расскажите о себе...",
            }
        ),
    )
    email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Телефон",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    github_url = forms.URLField(
        required=False,
        label="GitHub URL",
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )
    avatar = forms.ImageField(
        required=False,
        label="Аватар",
        widget=forms.FileInput(attrs={"class": "form-control-file"}),
    )

    class Meta:
        model = User
        fields = ["name", "surname", "about", "email", "phone", "github_url", "avatar"]

    def __init__(self, *args, **kwargs):
        """
        Инициализирует форму и заполняет поля name и surname из модели User.
        """
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["name"].initial = self.instance.first_name
            self.fields["surname"].initial = self.instance.last_name

    def save(self, commit=True):
        """
        Сохраняет изменения в модели User.

        Args:
            commit: Сохранять ли изменения в БД

        Returns:
            User: Объект пользователя с обновленными данными
        """
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("name", "")
        user.last_name = self.cleaned_data.get("surname", "")

        if commit:
            user.save()
        return user


class UpdateUserProfileForm(forms.ModelForm):
    """
    Форма для обновления профиля пользователя.

    URL: /users/edit-profile/

    Эта форма работает с моделью UserProfile и одновременно обновляет
    поля в связанной модели User (first_name, last_name).

    Поля из UserProfile:
        avatar: Аватар пользователя
        about: Информация о себе
        phone: Номер телефона
        github_url: Ссылка на GitHub

    Дополнительные поля:
        name: Имя (сохраняется в User.first_name)
        surname: Фамилия (сохраняется в User.last_name)
    """

    # Добавляем поля из базовой модели User
    name = forms.CharField(
        max_length=150,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    surname = forms.CharField(
        max_length=150,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = UserProfile
        fields = ["avatar", "about", "phone", "github_url"]
        widgets = {
            "about": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Расскажите о себе...",
                    "class": "form-control",
                }
            ),
            "phone": forms.TextInput(
                attrs={"placeholder": "+7 (999) 123-45-67", "class": "form-control"}
            ),
            "github_url": forms.URLInput(
                attrs={
                    "placeholder": "https://github.com/username",
                    "class": "form-control",
                }
            ),
            "avatar": forms.FileInput(
                attrs={"class": "avatar-input", "style": "display: none;"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Инициализирует форму с объектом пользователя.

        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы, включая user_instance
        """
        self.user_instance = kwargs.pop("user_instance", None)
        super().__init__(*args, **kwargs)

        # Заполняем поля name и surname из модели User
        if self.user_instance:
            # Для имени используем first_name или кастомное поле name
            if hasattr(self.user_instance, "name"):
                self.fields["name"].initial = self.user_instance.name
            else:
                self.fields["name"].initial = self.user_instance.first_name

            if hasattr(self.user_instance, "surname"):
                self.fields["surname"].initial = self.user_instance.surname
            else:
                self.fields["surname"].initial = self.user_instance.last_name

        # Добавляем CSS классы для всех полей
        for field_name, field in self.fields.items():
            if field_name != "avatar":
                if hasattr(field.widget, "input_type"):
                    if field.widget.input_type != "checkbox":
                        if "class" not in field.widget.attrs:
                            field.widget.attrs["class"] = "form-control"
                else:
                    if "class" not in field.widget.attrs:
                        field.widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        """
        Сохраняет изменения в UserProfile и User.

        Args:
            commit: Сохранять ли изменения в БД

        Returns:
            UserProfile: Объект профиля с обновленными данными
        """
        # Сохраняем профиль
        profile = super().save(commit=commit)

        # Сохраняем данные в модель User
        if self.user_instance:
            # Сохраняем имя
            if hasattr(self.user_instance, "name"):
                self.user_instance.name = self.cleaned_data.get("name", "")
            else:
                self.user_instance.first_name = self.cleaned_data.get("name", "")

            # Сохраняем фамилию
            if hasattr(self.user_instance, "surname"):
                self.user_instance.surname = self.cleaned_data.get("surname", "")
            else:
                self.user_instance.last_name = self.cleaned_data.get("surname", "")

            if commit:
                self.user_instance.save()

        return profile
