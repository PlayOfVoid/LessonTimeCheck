# Инструкция по развертыванию

## Подготовка к деплою

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Соберите статические файлы:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Выполните миграции:**
   ```bash
   python manage.py migrate
   ```

4. **Создайте суперпользователя (если нужно):**
   ```bash
   python manage.py createsuperuser
   ```

## Настройки для продакшена

### В `settings.py`:
- `DEBUG = False` - уже установлено
- `ALLOWED_HOSTS` - укажите ваш домен вместо `["*"]` для безопасности

### Настройка домена:
В `learn_time_check/settings.py` измените:
```python
ALLOWED_HOSTS = ["yourdomain.com", "www.yourdomain.com"]
```

## Запуск сервера

### Для разработки (локально):
```bash
python manage.py runserver 0.0.0.0:8000
```

### Для продакшена (рекомендуется использовать gunicorn):
```bash
pip install gunicorn
gunicorn learn_time_check.wsgi:application --bind 0.0.0.0:8000
```

### С помощью systemd (Linux):
Создайте файл `/etc/systemd/system/learntimecheck.service`:
```ini
[Unit]
Description=LearnTimeCheck Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/LearnTimeCheck
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn learn_time_check.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable learntimecheck
sudo systemctl start learntimecheck
```

## Настройка Nginx (опционально)

Создайте файл `/etc/nginx/sites-available/learntimecheck`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/LearnTimeCheck/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте:
```bash
sudo ln -s /etc/nginx/sites-available/learntimecheck /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Важные замечания

1. **Telegram токен и Chat ID** остаются в `settings.py` как задумано
2. **Статические файлы** обслуживаются через WhiteNoise автоматически
3. **База данных SQLite** находится в `db.sqlite3` - сделайте резервную копию
4. **Логирование** отключено в продакшене для оптимизации

## Проверка работы

1. Убедитесь, что сайт открывается
2. Проверьте, что статические файлы (CSS, JS) загружаются
3. Проверьте вход в систему
4. Создайте тестовое занятие и проверьте уведомления в Telegram

