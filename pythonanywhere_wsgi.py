"""
WSGI конфигурация для PythonAnywhere
Замените yourusername на ваш username на PythonAnywhere!
"""

import os
import sys

# Добавьте путь к вашему проекту
path = '/home/yourusername/LearnTimeCheck'  # ⚠️ ЗАМЕНИТЕ yourusername на ваш username!
if path not in sys.path:
    sys.path.insert(0, path)

# Установите переменные окружения
os.environ['DJANGO_SETTINGS_MODULE'] = 'learn_time_check.settings'

# Импортируем WSGI
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

application = StaticFilesHandler(get_wsgi_application())

