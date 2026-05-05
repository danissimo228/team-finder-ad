from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from users.models import UserProfile
from datetime import datetime


class Command(BaseCommand):
    help = "Create test users with their profiles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreate users even if they exist",
        )
        parser.add_argument(
            "--only-profile",
            action="store_true",
            help="Create only user profiles for existing users",
        )

    def handle(self, *args, **options):
        force = options["force"]
        only_profile = options["only_profile"]

        # Данные пользователей
        users_data = [
            {
                "username": "alexey_ivanov",
                "first_name": "Алексей",
                "last_name": "Иванов",
                "email": "alexey@example.com",
                "password": "qwerty",
                "is_staff": False,
                "is_superuser": False,
                "profile": {
                    "avatar": "avatars/alexey_avatar.jpg",
                    "about": "Python разработчик с 3-летним опытом. Люблю Django и создавать веб-приложения.",
                    "phone": "+7 (999) 123-45-67",
                    "github_url": "https://github.com/alexey-ivanov",
                },
            },
            {
                "username": "maria_petrova",
                "first_name": "Мария",
                "last_name": "Петрова",
                "email": "maria@example.com",
                "password": "qwerty1",
                "is_staff": True,
                "is_superuser": False,
                "profile": {
                    "avatar": "avatars/maria_avatar.jpg",
                    "about": "Team Lead и Full-stack разработчик. Увлекаюсь DevOps и оптимизацией процессов.",
                    "phone": "+7 (999) 234-56-78",
                    "github_url": "https://github.com/maria-petrova",
                },
            },
            {
                "username": "dmitry_smirnov",
                "first_name": "Дмитрий",
                "last_name": "Смирнов",
                "email": "dmitry@example.com",
                "password": "qwerty2",
                "is_staff": False,
                "is_superuser": False,
                "profile": {
                    "avatar": "",
                    "about": "Начинающий разработчик. Изучаю Python и Django. Открыт для сотрудничества!",
                    "phone": None,
                    "github_url": "https://github.com/dmitry-smirnov",
                },
            },
            {
                "username": "elena_volkova",
                "first_name": "Елена",
                "last_name": "Волкова",
                "email": "elena@example.com",
                "password": "qwerty3",
                "is_staff": False,
                "is_superuser": False,
                "profile": {
                    "avatar": "avatars/elena_avatar.jpg",
                    "about": "Frontend разработчик. React, Vue.js. Интересуюсь UI/UX дизайном.",
                    "phone": "+7 (999) 345-67-89",
                    "github_url": "https://github.com/elena-volkova",
                },
            },
            {
                "username": "admin",
                "first_name": "Админ",
                "last_name": "Админов",
                "email": "admin@example.com",
                "password": "qwerty4",
                "is_staff": True,
                "is_superuser": True,
                "profile": {
                    "avatar": "",
                    "about": "Системный администратор и разработчик. Отвечаю за инфраструктуру проекта.",
                    "phone": "+7 (999) 456-78-90",
                    "github_url": "https://github.com/admin",
                },
            },
        ]

        if only_profile:
            self.create_profiles(users_data, force)
        else:
            self.create_users_and_profiles(users_data, force)

    def create_users_and_profiles(self, users_data, force):
        """Создает пользователей и их профили"""
        for user_data in users_data:
            username = user_data["username"]

            # Проверяем существует ли пользователь
            user_exists = User.objects.filter(username=username).exists()

            if user_exists and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Пользователь {username} уже существует. Используйте --force для перезаписи."
                    )
                )
                continue

            if user_exists and force:
                # Удаляем существующего пользователя (профиль удалится каскадно)
                User.objects.filter(username=username).delete()
                self.stdout.write(f"Удален существующий пользователь {username}")

            # Создаем пользователя с помощью create_user (автоматически хэширует пароль)
            user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_staff=user_data["is_staff"],
                is_superuser=user_data["is_superuser"],
            )

            # Создаем профиль
            profile_data = user_data["profile"]
            profile = UserProfile(
                user=user,
                avatar=profile_data["avatar"] if profile_data["avatar"] else None,
                about=profile_data["about"],
                phone=profile_data["phone"],
                github_url=profile_data["github_url"],
            )
            profile.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Создан пользователь: {username} (пароль: {user_data["password"]})'
                )
            )

    def create_profiles(self, users_data, force):
        """Создает только профили для существующих пользователей"""
        for user_data in users_data:
            username = user_data["username"]

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Пользователь {username} не существует. Сначала создайте пользователя."
                    )
                )
                continue

            # Проверяем существует ли профиль
            profile_exists = UserProfile.objects.filter(user=user).exists()

            if profile_exists and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Профиль для {username} уже существует. Используйте --force для обновления."
                    )
                )
                continue

            if profile_exists and force:
                UserProfile.objects.filter(user=user).delete()
                self.stdout.write(f"Удален существующий профиль для {username}")

            # Создаем профиль
            profile_data = user_data["profile"]
            profile = UserProfile(
                user=user,
                avatar=profile_data["avatar"] if profile_data["avatar"] else None,
                about=profile_data["about"],
                phone=profile_data["phone"],
                github_url=profile_data["github_url"],
            )
            profile.save()

            self.stdout.write(self.style.SUCCESS(f"✓ Создан профиль для: {username}"))
