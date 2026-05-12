# admin.py
from django.contrib.admin import AdminSite
from django.core.cache import cache
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from datetime import datetime, timedelta
from collections import Counter
from projects.models import Project
from users.models import UserProfile
from django.contrib.auth.models import User


class StatsAdminSite(AdminSite):
    """Кастомный AdminSite со страницей статистики"""
    
    site_header = 'Мой Админ-панель'
    site_title = 'Админ-панель'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('request-stats/', self.admin_view(self.request_stats_view), name='request_stats'),
        ]
        return custom_urls + urls
    
    @method_decorator(staff_member_required)
    def request_stats_view(self, request):
        """Отображение статистики запросов"""
        
        # Получаем статистику из кеша
        stats = cache.get('stats', [])
        
        # Статистика за все время
        total_requests = len(stats)
        
        # Статистика по методам
        methods_counter = Counter(entry.get('method', 'UNKNOWN') for entry in stats)
        # Преобразуем в список словарей для шаблона
        methods = [
            {'method': method, 'count': count, 'percentage': (count / total_requests * 100) if total_requests > 0 else 0}
            for method, count in methods_counter.items()
        ]
        
        # Статистика по статусам
        status_counter = Counter(entry.get('status_code', 0) for entry in stats)
        status_codes = [
            {'code': code, 'count': count, 'percentage': (count / total_requests * 100) if total_requests > 0 else 0}
            for code, count in status_counter.items()
        ]
        
        # Топ URL
        url_counter = Counter()
        for entry in stats:
            path = entry.get('path', '')
            method = entry.get('method', '')
            url_counter[f"{method} {path}"] += 1
        top_urls = [{'url': url, 'count': count} for url, count in url_counter.most_common(10)]
        
        # Топ IP адресов
        ip_counter = Counter(entry.get('ip_address', 'unknown') for entry in stats)
        top_ips = [{'ip': ip, 'count': count} for ip, count in ip_counter.most_common(10)]
        
        # Средняя длительность запроса
        durations = [entry.get('duration_seconds', 0) for entry in stats if entry.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Статистика за последний час
        one_hour_ago = timezone.now() - timedelta(hours=1)
        last_hour_requests = [
            entry for entry in stats 
            if datetime.fromisoformat(entry['timestamp']) >= one_hour_ago.replace(tzinfo=None)
        ]
        
        # Статистика по ошибкам
        errors = [entry for entry in stats if entry.get('error') or entry.get('status_code', 200) >= 400]
        error_rate = (len(errors) / total_requests * 100) if total_requests > 0 else 0
        
        # Пользователи
        users_counter = Counter(entry.get('username', 'Аноним') for entry in stats if entry.get('username'))
        popular_users = [{'username': user, 'count': count} for user, count in users_counter.most_common(5)]
        
        # График запросов по часам (последние 24 часа)
        hours_data = self._get_hourly_stats(stats)
        
        # Подготовка данных для графика (преобразуем в JSON)
        import json
        hours_json = json.dumps(list(hours_data.values()))
        
        context = {
            'title': 'Статистика запросов',
            'total_requests': total_requests,
            'methods': methods,
            'status_codes': status_codes,
            'top_urls': top_urls,
            'top_ips': top_ips,
            'avg_duration': avg_duration,
            'last_hour_requests': len(last_hour_requests),
            'error_rate': error_rate,
            'errors_count': len(errors),
            'popular_users': popular_users,
            'hours_data': hours_data,
            'hours_json': hours_json,  # Для JavaScript
            'recent_requests': stats[:20],  # Последние 20 запросов
        }
        
        return render(request, 'admin/request_stats.html', context)
    
    def _get_hourly_stats(self, stats):
        """Группировка запросов по часам за последние 24 часа"""
        hourly_counts = {i: 0 for i in range(24)}
        
        now = timezone.now()
        current_date = now.date()
        
        for entry in stats[:500]:  # Ограничиваем для производительности
            try:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                # Сравниваем только дату, игнорируя часовой пояс
                if timestamp.date() == current_date:
                    hour = timestamp.hour
                    hourly_counts[hour] += 1
            except (ValueError, KeyError):
                continue
        
        return hourly_counts


# Создаем экземпляр кастомного админ-сайта
admin_site = StatsAdminSite(name='myadmin')
admin_site.register(UserProfile)
admin_site.register(Project)
admin_site.register(User)