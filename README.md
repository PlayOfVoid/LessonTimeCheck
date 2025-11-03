# LearnTimeCheck

Простой сайт на Django для добавления занятий и авто-уведомлений в Telegram за 60 минут и за 5 минут до начала.

## Запуск (Windows PowerShell)

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Инициализация БД
python manage.py migrate

# (опционально) Создать администратора
python manage.py createsuperuser

# Запуск сервера (уведомления запускаются автоматически в фоне)
python manage.py runserver
```

Откройте http://127.0.0.1:8000/ — добавляйте занятия через форму; все занятия отображаются в таблице.

## Переменные окружения

По умолчанию используются значения из `settings.py`:
- `TELEGRAM_BOT_TOKEN` — токен бота
- `TELEGRAM_CHAT_ID` — ваш chat id

Можно переопределить:

```powershell
$env:TELEGRAM_BOT_TOKEN = "<token>"
$env:TELEGRAM_CHAT_ID = "1965639178"
```

## Примечания
- Планировщик уведомлений стартует в `lessons.apps.LessonsConfig.ready()` и работает в отдельном потоке. Проверяет каждые 30 секунд.
- Часовой пояс по умолчанию — `Europe/Moscow`. Вводится локальное время, далее приводится к aware datetime.
- Флаги `notified_one_hour` и `notified_five_minutes` защищают от повторных отправок.


