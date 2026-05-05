from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projects.models import Project
from datetime import datetime


class Command(BaseCommand):
    help = "Create test projects with their relationships"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreate projects even if they exist",
        )
        parser.add_argument(
            "--user",
            type=str,
            help="Create projects only for specific username",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing projects before creating",
        )

    def handle(self, *args, **options):
        force = options["force"]
        username = options["user"]
        clear = options["clear"]

        # Данные проектов
        projects_data = [
            {
                "name": "Корпоративный портал",
                "description": "Внутренний портал для сотрудников компании с системой документооборота, календарем и задачами.",
                "github_url": "https://github.com/company/corporate-portal",
                "status": "in_progress",
                "owner_username": "alexey_ivanov",
                "participants_usernames": [
                    "alexey_ivanov",
                    "maria_petrova",
                    "dmitry_smirnov",
                ],
            },
            {
                "name": "Интернет-магазин",
                "description": "Платформа для онлайн-продаж с интеграцией платежных систем и CRM.",
                "github_url": "https://github.com/company/e-shop",
                "status": "open",
                "owner_username": "maria_petrova",
                "participants_usernames": [
                    "maria_petrova",
                    "alexey_ivanov",
                    "elena_volkova",
                ],
            },
            {
                "name": "Мобильное приложение",
                "description": "Кроссплатформенное мобильное приложение для клиентов компании.",
                "github_url": "https://github.com/company/mobile-app",
                "status": "in_progress",
                "owner_username": "dmitry_smirnov",
                "participants_usernames": ["dmitry_smirnov", "elena_volkova"],
            },
            {
                "name": "CRM система",
                "description": "Система управления взаимоотношениями с клиентами с аналитикой и отчетами.",
                "github_url": "https://github.com/company/crm",
                "status": "closed",
                "owner_username": "elena_volkova",
                "participants_usernames": ["elena_volkova", "maria_petrova"],
            },
            {
                "name": "API Gateway",
                "description": "Центральный шлюз для микросервисной архитектуры с аутентификацией и маршрутизацией.",
                "github_url": "https://github.com/company/api-gateway",
                "status": "completed",
                "owner_username": "admin",
                "participants_usernames": ["admin", "alexey_ivanov"],
            },
            {
                "name": "Аналитическая платформа",
                "description": "Система сбора и визуализации данных с дашбордами и отчетностью.",
                "github_url": "https://github.com/company/analytics",
                "status": "open",
                "owner_username": "maria_petrova",
                "participants_usernames": ["maria_petrova", "dmitry_smirnov", "admin"],
            },
            {
                "name": "Чат-бот поддержки",
                "description": "AI-powered чат-бот для автоматизации поддержки клиентов.",
                "github_url": "https://github.com/company/support-bot",
                "status": "in_progress",
                "owner_username": "alexey_ivanov",
                "participants_usernames": ["alexey_ivanov", "elena_volkova"],
            },
            {
                "name": "DevOps платформа",
                "description": "Инструменты для CI/CD, мониторинга и управления инфраструктурой.",
                "github_url": "https://github.com/company/devops-platform",
                "status": "in_progress",
                "owner_username": "admin",
                "participants_usernames": ["admin", "maria_petrova", "dmitry_smirnov"],
            },
        ]

        if clear:
            self.clear_projects(username)

        if username:
            projects_data = [
                p for p in projects_data if p["owner_username"] == username
            ]
            if not projects_data:
                self.stdout.write(
                    self.style.WARNING(f"Нет проектов для пользователя {username}")
                )
                return

        self.create_projects(projects_data, force)

    def clear_projects(self, username=None):
        """Очищает существующие проекты"""
        if username:
            try:
                user = User.objects.get(username=username)
                count = Project.objects.filter(owner=user).count()
                Project.objects.filter(owner=user).delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Удалено {count} проектов пользователя {username}"
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Пользователь {username} не существует")
                )
        else:
            count = Project.objects.all().count()
            Project.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Удалено {count} проектов"))

    def create_projects(self, projects_data, force):
        """Создает проекты"""
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for project_data in projects_data:
            project_name = project_data["name"]
            username = project_data["owner_username"]

            # Получаем владельца
            try:
                owner = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'Пользователь {username} не существует. Пропускаем проект "{project_name}"'
                    )
                )
                skipped_count += 1
                continue

            # Проверяем существует ли проект
            project_exists = Project.objects.filter(name=project_name).exists()

            if project_exists and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f'Проект "{project_name}" уже существует. Используйте --force для перезаписи.'
                    )
                )
                skipped_count += 1
                continue

            if project_exists and force:
                # Обновляем существующий проект
                project = Project.objects.get(name=project_name)
                project.description = project_data["description"]
                project.github_url = project_data.get("github_url", "")
                project.status = project_data["status"]
                project.owner = owner
                project.save()

                # Обновляем участников
                project.participants.clear()
                for participant_username in project_data["participants_usernames"]:
                    try:
                        participant = User.objects.get(username=participant_username)
                        project.participants.add(participant)
                    except User.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Участник {participant_username} не найден для проекта {project_name}"
                            )
                        )

                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Обновлен проект: {project_name}")
                )
            else:
                # Создаем новый проект
                project = Project(
                    name=project_data["name"],
                    description=project_data["description"],
                    github_url=project_data.get("github_url", ""),
                    status=project_data["status"],
                    owner=owner,
                )
                project.save()

                # Добавляем участников
                for participant_username in project_data["participants_usernames"]:
                    try:
                        participant = User.objects.get(username=participant_username)
                        project.participants.add(participant)
                    except User.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Участник {participant_username} не найден для проекта {project_name}"
                            )
                        )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Создан проект: {project_name} (владелец: {username})"
                    )
                )

                # Выводим участников
                if len(project_data["participants_usernames"]) > 1:
                    participants_str = ", ".join(project_data["participants_usernames"])
                    self.stdout.write(f"    Участники: {participants_str}")

        # Выводим статистику
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"Статистика создания проектов:"))
        self.stdout.write(f"  Создано: {created_count}")
        self.stdout.write(f"  Обновлено: {updated_count}")
        self.stdout.write(f"  Пропущено: {skipped_count}")
        self.stdout.write("=" * 50)
