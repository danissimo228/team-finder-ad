"""
Формы для управления пользователями, включая регистрацию, аутентификацию и редактирование профиля.
"""

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import User

from users.models import UserInfo

# Константы для валидации полей
MIN_PASSWORD_LENGTH = 6
MAX_NAME_LENGTH = 30
MAX_SURNAME_LENGTH = 30
MAX_NAME_LENGTH_PROFILE = 150
MAX_SURNAME_LENGTH_PROFILE = 150
MAX_PHONE_LENGTH = 20

# Константы для Textarea
ABOUT_ROWS = 5
ABOUT_ROWS_PROFILE = 4

# Константы для placeholder'ов
NAME_PLACEHOLDER = "Введите имя"
SURNAME_PLACEHOLDER = "Введите фамилию"
EMAIL_PLACEHOLDER = "example@mail.com"
PASSWORD_PLACEHOLDER = "Введите пароль"
OLD_PASSWORD_PLACEHOLDER = "Введите текущий пароль"
NEW_PASSWORD_PLACEHOLDER = "Введите новый пароль"
CONFIRM_PASSWORD_PLACEHOLDER = "Подтвердите новый пароль"
ABOUT_PLACEHOLDER = "Расскажите о себе..."
PHONE_PLACEHOLDER = "+7 (999) 123-45-67"
GITHUB_PLACEHOLDER = "https://github.com/username"

# Константы для CSS классов
CSS_CLASS_FORM_CONTROL = "form-control"
CSS_CLASS_AVATAR_INPUT = "avatar-input"
CSS_CLASS_FORM_CONTROL_FILE = "form-control-file"
CSS_AVATAR_INPUT_STYLE = "display: none;"

# Константы для сообщений об ошибках
ERROR_EMAIL_EXISTS = "Пользователь с таким email уже существует"
ERROR_NAME_NOT_ALPHA = "Имя должно содержать только буквы"
ERROR_SURNAME_NOT_ALPHA = "Фамилия должна содержать только буквы"
ERROR_PASSWORD_TOO_SHORT = (
    f"Пароль должен содержать минимум {MIN_PASSWORD_LENGTH} символов"
)
ERROR_INVALID_CREDENTIALS = "Неверный email или пароль"
ERROR_ACCOUNT_NOT_ACTIVE = "Учетная запись не активирована"
ERROR_USER_NOT_FOUND = "Пользователь с таким email не найден"
ERROR_INVALID_OLD_PASSWORD = "Неверный текущий пароль"
ERROR_PASSWORDS_MISMATCH = "Пароли не совпадают"


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
        max_length=MAX_NAME_LENGTH,
        label="Имя",
        widget=forms.TextInput(attrs={"placeholder": NAME_PLACEHOLDER}),
    )
    surname = forms.CharField(
        max_length=MAX_SURNAME_LENGTH,
        label="Фамилия",
        widget=forms.TextInput(attrs={"placeholder": SURNAME_PLACEHOLDER}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": EMAIL_PLACEHOLDER}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": PASSWORD_PLACEHOLDER}),
    )

    def clean_email(self):
        """Проверяет, что email не используется другим пользователем."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(ERROR_EMAIL_EXISTS)
        return email

    def clean_name(self):
        """Проверяет, что имя содержит только буквы."""
        name = self.cleaned_data.get("name")
        if not name.isalpha():
            raise forms.ValidationError(ERROR_NAME_NOT_ALPHA)
        return name

    def clean_surname(self):
        """Проверяет, что фамилия содержит только буквы."""
        surname = self.cleaned_data.get("surname")
        if not surname.isalpha():
            raise forms.ValidationError(ERROR_SURNAME_NOT_ALPHA)
        return surname

    def clean_password(self):
        """Проверяет, что пароль соответствует требованиям безопасности."""
        password = self.cleaned_data.get("password")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise forms.ValidationError(ERROR_PASSWORD_TOO_SHORT)
        return password

    def save(self, request):
        """
        Создает нового пользователя и информацию о нем.

        Args:
            request: HTTP request object для выполнения входа

        Returns:
            User: Созданный объект пользователя
        """
        name = self.cleaned_data["name"]
        surname = self.cleaned_data["surname"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        # Генерируем username из email
        username = email.split("@")[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count()}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name,
            last_name=surname,
        )
        UserInfo.objects.create(user=user)

        return user


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
            attrs={"placeholder": EMAIL_PLACEHOLDER, "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": PASSWORD_PLACEHOLDER}),
    )

    def clean(self):
        """
        Проверяет учетные данные пользователя.

        Аутентифицирует пользователя по email и паролю.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
                if user is None:
                    raise forms.ValidationError(ERROR_INVALID_CREDENTIALS)
                if not user.is_active:
                    raise forms.ValidationError(ERROR_ACCOUNT_NOT_ACTIVE)
                cleaned_data["user"] = user
            except User.DoesNotExist:
                raise forms.ValidationError(ERROR_USER_NOT_FOUND)

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
        widget=forms.PasswordInput(attrs={"placeholder": OLD_PASSWORD_PLACEHOLDER}),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={"placeholder": NEW_PASSWORD_PLACEHOLDER}),
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={"placeholder": CONFIRM_PASSWORD_PLACEHOLDER}),
    )

    def __init__(self, user, *args, **kwargs):
        """Инициализирует форму с объектом пользователя."""
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """Проверяет правильность текущего пароля."""
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError(ERROR_INVALID_OLD_PASSWORD)
        return old_password

    def clean_new_password2(self):
        """
        Проверяет совпадение нового пароля и его подтверждения,
        а также валидность пароля.
        """
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError(ERROR_PASSWORDS_MISMATCH)

        if new_password1:
            try:
                password_validation.validate_password(new_password1, self.user)
            except forms.ValidationError as e:
                self.add_error("new_password1", e)

        return new_password2

    def save(self, commit=True):
        """Сохраняет новый пароль для пользователя."""
        new_password = self.cleaned_data.get("new_password1")
        self.user.set_password(new_password)
        if commit:
            self.user.save()
        return self.user


class UserProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя (устаревшая).

    Note:
        Эта форма устарела. Используйте UpdateUserInfoForm.
    """

    name = forms.CharField(
        max_length=MAX_NAME_LENGTH,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )
    surname = forms.CharField(
        max_length=MAX_SURNAME_LENGTH,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )
    about = forms.CharField(
        required=False,
        label="О себе",
        widget=forms.Textarea(
            attrs={
                "class": CSS_CLASS_FORM_CONTROL,
                "rows": ABOUT_ROWS,
                "placeholder": ABOUT_PLACEHOLDER,
            }
        ),
    )
    email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )
    phone = forms.CharField(
        max_length=MAX_PHONE_LENGTH,
        required=False,
        label="Телефон",
        widget=forms.TextInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )
    github_url = forms.URLField(
        required=False,
        label="GitHub URL",
        widget=forms.URLInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )
    avatar = forms.ImageField(
        required=False,
        label="Аватар",
        widget=forms.FileInput(attrs={"class": CSS_CLASS_FORM_CONTROL_FILE}),
    )

    class Meta:
        model = User
        fields = ["name", "surname", "about", "email", "phone", "github_url", "avatar"]

    def __init__(self, *args, **kwargs):
        """Инициализирует форму и заполняет поля name и surname из модели User."""
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["name"].initial = self.instance.first_name
            self.fields["surname"].initial = self.instance.last_name

    def save(self, commit=True):
        """Сохраняет изменения в модели User."""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("name", "")
        user.last_name = self.cleaned_data.get("surname", "")
        user.email = self.cleaned_data.get("email", user.email)

        if commit:
            user.save()
            # Сохраняем информацию о пользователе
            user_info, _ = UserInfo.objects.get_or_create(user=user)
            user_info.about = self.cleaned_data.get("about", "")
            user_info.phone = self.cleaned_data.get("phone", "")
            user_info.github_url = self.cleaned_data.get("github_url", "")
            if self.cleaned_data.get("avatar"):
                user_info.avatar = self.cleaned_data.get("avatar")
            user_info.save()

        return user


class UpdateUserInfoForm(forms.ModelForm):
    """
    Форма для обновления информации о пользователе.

    Эта форма работает с моделью UserInfo и одновременно обновляет
    поля в связанной модели User (first_name, last_name).
    """

    name = forms.CharField(
        max_length=MAX_NAME_LENGTH_PROFILE,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )
    surname = forms.CharField(
        max_length=MAX_SURNAME_LENGTH_PROFILE,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": CSS_CLASS_FORM_CONTROL}),
    )

    class Meta:
        model = UserInfo
        fields = ["avatar", "about", "phone", "github_url"]
        widgets = {
            "about": forms.Textarea(
                attrs={
                    "rows": ABOUT_ROWS_PROFILE,
                    "placeholder": ABOUT_PLACEHOLDER,
                    "class": CSS_CLASS_FORM_CONTROL,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": PHONE_PLACEHOLDER,
                    "class": CSS_CLASS_FORM_CONTROL,
                }
            ),
            "github_url": forms.URLInput(
                attrs={
                    "placeholder": GITHUB_PLACEHOLDER,
                    "class": CSS_CLASS_FORM_CONTROL,
                }
            ),
            "avatar": forms.FileInput(
                attrs={
                    "class": CSS_CLASS_AVATAR_INPUT,
                    "style": CSS_AVATAR_INPUT_STYLE,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Инициализирует форму с объектом пользователя."""
        self.user_instance = kwargs.pop("user_instance", None)
        super().__init__(*args, **kwargs)

        if self.user_instance:
            self.fields["name"].initial = self.user_instance.first_name
            self.fields["surname"].initial = self.user_instance.last_name

        for field_name, field in self.fields.items():
            if field_name != "avatar":
                if "class" not in field.widget.attrs:
                    field.widget.attrs["class"] = CSS_CLASS_FORM_CONTROL

    def save(self, commit=True):
        """Сохраняет изменения в UserInfo и User."""
        user_info = super().save(commit=commit)

        if self.user_instance:
            self.user_instance.first_name = self.cleaned_data.get("name", "")
            self.user_instance.last_name = self.cleaned_data.get("surname", "")

            if commit:
                self.user_instance.save()

        return user_info


class FullUser:
    def __init__(self, user: User):
        self.id = user.id
        self.username = user.username
        self.email = user.email
        self.first_name = user.first_name or ""
        self.last_name = user.last_name or ""

        self.name = user.first_name or user.username
        self.surname = user.last_name or ""

        try:
            user_info = user.info
            self.avatar = user_info.avatar
            self.phone = user_info.phone
            self.github_url = user_info.github_url
            self.about = user_info.about or ""
            self.owned_projects = user.owned_projects
        except UserInfo.DoesNotExist:
            self.avatar = None
            self.phone = None
            self.github_url = None
            self.about = ""

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
