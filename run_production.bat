@echo off
REM Скрипт для запуска сервера в режиме продакшена
echo Запуск сервера в режиме продакшена...
set DJANGO_DEBUG=false
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
pause

