import os
import threading
import time
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from .models import Lesson

_notifier_started = False
_lock = threading.Lock()


def _send_message(text: str) -> bool:
    try:
        import telebot

        bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode=None)
        bot.send_message(settings.TELEGRAM_CHAT_ID, text)
        return True
    except Exception as e:
        # Avoid crashing background loop on network / API errors
        # В режиме разработки можно раскомментировать для отладки:
        # print(f"Ошибка отправки Telegram: {e}")
        return False


def _format_username(username: str) -> str:
    if not username:
        return ""
    if username.startswith("@"):  # keep single @
        return username
    return f"@{username}"


def _notifier_loop() -> None:
    while True:
        try:
            # Ensure DB connections are valid in this background thread
            close_old_connections()
            now = timezone.now()
            # Tolerance window of +/- 60 seconds around target moments
            lower = now - timedelta(seconds=60)
            upper = now + timedelta(seconds=60)

            # 60 minutes notice (используем точно такую же формулу, как для 5 минут)
            qs_1h = Lesson.objects.filter(
                start_time__gte=lower + timedelta(hours=1),
                start_time__lte=upper + timedelta(hours=1),
                notified_one_hour=False,
            )
            for lesson in qs_1h:
                try:
                    local_time = timezone.localtime(lesson.start_time)
                    msg = (
                        f"занятие в {local_time.strftime('%H:%M')} через час у '{lesson.student_name}' "
                        f"{_format_username(lesson.tg_username)}"
                    )
                    if _send_message(msg):
                        lesson.notified_one_hour = True
                        lesson.save(update_fields=["notified_one_hour", "updated_at"])
                except Exception as e:
                    # Пропускаем конкретное занятие при ошибке, но продолжаем проверку
                    # В режиме разработки можно раскомментировать print для отладки
                    # print(f"Ошибка при отправке уведомления за час: {e}")
                    pass

            # 5 minutes notice
            qs_5m = Lesson.objects.filter(
                start_time__gte=lower + timedelta(minutes=5),
                start_time__lte=upper + timedelta(minutes=5),
                notified_five_minutes=False,
            )
            for lesson in qs_5m:
                try:
                    local_time = timezone.localtime(lesson.start_time)
                    msg = (
                        f"занятие в {local_time.strftime('%H:%M')} через 5 минут у '{lesson.student_name}' "
                        f"{_format_username(lesson.tg_username)}"
                    )
                    if _send_message(msg):
                        lesson.notified_five_minutes = True
                        lesson.save(update_fields=["notified_five_minutes", "updated_at"])
                except Exception:
                    pass

        except Exception:
            # Never let the loop die; swallow but continue next cycle
            # (Intentionally minimal logging to keep console clean on dev server)
            pass
        finally:
            # Close any stale connections and wait before next cycle
            try:
                close_old_connections()
            finally:
                time.sleep(10)  # Проверяем каждые 10 секунд для надежности


def start_notifier_once() -> None:
    global _notifier_started
    with _lock:
        # Avoid duplicate thread in autoreloader
        run_main = os.environ.get("RUN_MAIN") == "true"
        if _notifier_started or (not run_main and settings.DEBUG):
            return
        t = threading.Thread(target=_notifier_loop, name="lesson-notifier", daemon=True)
        t.start()
        _notifier_started = True


