# middleware.py
import json
import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.urls import resolve

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования всех запросов в кеш.
    Сохраняет информацию о запросах в cache под ключом 'stats'
    """

    # Максимальное количество записей в истории
    MAX_STATS_HISTORY = 1000

    def process_request(self, request):
        """Сохраняем время начала обработки запроса"""
        request.start_time = datetime.now()

    def process_response(self, request, response):
        """Логируем информацию о запросе и ответе"""
        try:
            # Получаем текущую статистику из кеша
            stats = cache.get("stats", [])

            # Создаем запись о запросе
            log_entry = self._create_log_entry(request, response)

            # Добавляем новую запись в начало списка (свежие сверху)
            stats.insert(0, log_entry)

            # Ограничиваем размер истории
            if len(stats) > self.MAX_STATS_HISTORY:
                stats = stats[: self.MAX_STATS_HISTORY]

            # Сохраняем обратно в кеш (время жизни 24 часа)
            print(stats)
            print("!" * 100)
            cache.set("stats", stats, timeout=86400)

        except Exception as e:
            logger.error(f"Ошибка при логировании запроса: {e}")

        return response

    def process_exception(self, request, exception):
        """Логируем информацию об исключении"""
        try:
            stats = cache.get("stats", [])

            log_entry = self._create_error_log_entry(request, exception)
            stats.insert(0, log_entry)

            if len(stats) > self.MAX_STATS_HISTORY:
                stats = stats[: self.MAX_STATS_HISTORY]

            cache.set("stats", stats, timeout=86400)

        except Exception as e:
            logger.error(f"Ошибка при логировании исключения: {e}")

        return None

    def _create_log_entry(self, request, response):
        """Создание записи лога для успешного запроса"""
        # Получаем IP адрес клиента
        ip = self._get_client_ip(request)

        # Получаем имя пользователя если авторизован
        username = None
        if hasattr(request, "user") and request.user.is_authenticated:
            username = request.user.username

        # Вычисляем время выполнения запроса
        duration = None
        if hasattr(request, "start_time"):
            duration = (datetime.now() - request.start_time).total_seconds()

        # Получаем имя view функции
        view_name = None
        try:
            match = resolve(request.path)
            view_name = f"{match.func.__module__}.{match.func.__name__}"
        except Exception:
            view_name = None

        # Формируем запись
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.path,
            "full_path": request.get_full_path(),
            "query_string": request.META.get("QUERY_STRING", ""),
            "ip_address": ip,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "referer": request.META.get("HTTP_REFERER", ""),
            "username": username,
            "status_code": response.status_code,
            "response_size": len(response.content)
            if hasattr(response, "content")
            else 0,
            "duration_seconds": duration,
            "view_name": view_name,
        }

        return log_entry

    def _create_error_log_entry(self, request, exception):
        """Создание записи лога для запроса с исключением"""
        ip = self._get_client_ip(request)

        username = None
        if hasattr(request, "user") and request.user.is_authenticated:
            username = request.user.username

        duration = None
        if hasattr(request, "start_time"):
            duration = (datetime.now() - request.start_time).total_seconds()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.path,
            "full_path": request.get_full_path(),
            "query_string": request.META.get("QUERY_STRING", ""),
            "ip_address": ip,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "referer": request.META.get("HTTP_REFERER", ""),
            "username": username,
            "status_code": 500,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "duration_seconds": duration,
            "error": True,
        }

        return log_entry

    def _get_client_ip(self, request):
        """Получение реального IP адреса клиента с учетом прокси"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
