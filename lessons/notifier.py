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


def _send_message_to_chat(text: str, chat_id: str) -> bool:
    """Отправить сообщение в Telegram на указанный chat_id"""
    if not chat_id:
        if settings.DEBUG:
            print(f"[NOTIFIER] Пропуск: chat_id не указан")
        return False
    try:
        import telebot

        bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode=None)
        bot.send_message(chat_id, text)
        if settings.DEBUG:
            print(f"[NOTIFIER] ✅ Сообщение отправлено: {text[:50]}...")
        return True
    except Exception as e:
        if settings.DEBUG:
            print(f"[NOTIFIER] ❌ Ошибка отправки Telegram: {e}")
        return False


def _format_username(username: str) -> str:
    if not username:
        return ""
    if username.startswith("@"):  # keep single @
        return username
    return f"@{username}"


def _notifier_loop() -> None:
    if settings.DEBUG:
        print("[NOTIFIER] 🚀 Запуск фонового потока уведомлений")
    iteration = 0
    while True:
        try:
            # Ensure DB connections are valid in this background thread
            close_old_connections()
            now = timezone.now()
            now_local = timezone.localtime(now)
            
            iteration += 1
            if settings.DEBUG and iteration % 12 == 0:  # Каждые ~2 минуты выводим статус
                print(f"[NOTIFIER] 💓 Работаю... Текущее время: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Увеличиваем окно проверки до 2 минут для надежности
            window_seconds = 120  # 2 минуты
            lower = now - timedelta(seconds=window_seconds)
            upper = now + timedelta(seconds=window_seconds)

            # 60 минут (1 час) до начала занятия
            # Проверяем занятия, которые начинаются через 1 час (с допуском ±2 минуты)
            target_time_1h_lower = now + timedelta(hours=1, minutes=-2)  # 58 минут
            target_time_1h_upper = now + timedelta(hours=1, minutes=2)    # 62 минуты
            
            qs_1h = Lesson.objects.filter(
                start_time__gte=target_time_1h_lower,
                start_time__lte=target_time_1h_upper,
                notified_one_hour=False,
            )
            
            for lesson in qs_1h:
                try:
                    if not lesson.teacher.telegram_chat_id:
                        if settings.DEBUG:
                            print(f"[NOTIFIER] ⚠️ Пропуск урока {lesson.id}: нет telegram_chat_id у учителя")
                        continue
                    
                    lesson_time = timezone.localtime(lesson.start_time)
                    time_diff = (lesson.start_time - now).total_seconds() / 60  # разница в минутах
                    
                    if settings.DEBUG:
                        print(f"[NOTIFIER] 📨 Найдено занятие за час: {lesson.student.name} в {lesson_time.strftime('%H:%M')} (через {time_diff:.1f} мин)")
                    
                    msg = f"занятие в {lesson_time.strftime('%H:%M')} через час у '{lesson.student.name}'"
                    
                    if _send_message_to_chat(msg, lesson.teacher.telegram_chat_id):
                        if settings.DEBUG:
                            print(f"[NOTIFIER] 🗑️ Удаление занятия {lesson.id} после отправки уведомления за час")
                        lesson.delete()
                    else:
                        if settings.DEBUG:
                            print(f"[NOTIFIER] ⚠️ Не удалось отправить уведомление за час для занятия {lesson.id}")
                except Exception as e:
                    if settings.DEBUG:
                        print(f"[NOTIFIER] ❌ Ошибка при обработке уведомления за час: {e}")
                        import traceback
                        traceback.print_exc()

            # 5 минут до начала занятия
            # Проверяем занятия, которые начинаются через 5 минут (с допуском ±2 минуты)
            target_time_5m_lower = now + timedelta(minutes=3)  # 3 минуты
            target_time_5m_upper = now + timedelta(minutes=7)  # 7 минут
            
            qs_5m = Lesson.objects.filter(
                start_time__gte=target_time_5m_lower,
                start_time__lte=target_time_5m_upper,
                notified_five_minutes=False,
            )
            
            for lesson in qs_5m:
                try:
                    if not lesson.teacher.telegram_chat_id:
                        if settings.DEBUG:
                            print(f"[NOTIFIER] ⚠️ Пропуск урока {lesson.id}: нет telegram_chat_id у учителя")
                        continue
                    
                    lesson_time = timezone.localtime(lesson.start_time)
                    time_diff = (lesson.start_time - now).total_seconds() / 60  # разница в минутах
                    
                    if settings.DEBUG:
                        print(f"[NOTIFIER] 📨 Найдено занятие за 5 минут: {lesson.student.name} в {lesson_time.strftime('%H:%M')} (через {time_diff:.1f} мин)")
                    
                    msg = f"занятие в {lesson_time.strftime('%H:%M')} через 5 минут у '{lesson.student.name}'"
                    
                    if _send_message_to_chat(msg, lesson.teacher.telegram_chat_id):
                        lesson.notified_five_minutes = True
                        lesson.save(update_fields=["notified_five_minutes", "updated_at"])
                        if settings.DEBUG:
                            print(f"[NOTIFIER] ✅ Уведомление за 5 минут отправлено для занятия {lesson.id}")
                    else:
                        if settings.DEBUG:
                            print(f"[NOTIFIER] ⚠️ Не удалось отправить уведомление за 5 минут для занятия {lesson.id}")
                except Exception as e:
                    if settings.DEBUG:
                        print(f"[NOTIFIER] ❌ Ошибка при обработке уведомления за 5 минут: {e}")
                        import traceback
                        traceback.print_exc()

        except Exception as e:
            if settings.DEBUG:
                print(f"[NOTIFIER] ❌ Критическая ошибка в цикле уведомлений: {e}")
                import traceback
                traceback.print_exc()
        finally:
            # Close any stale connections and wait before next cycle
            try:
                close_old_connections()
            finally:
                time.sleep(10)  # Проверяем каждые 10 секунд


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


