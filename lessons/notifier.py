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
        print(f"[NOTIFIER ERROR] Chat ID не указан для отправки сообщения")
        return False
    
    # Проверяем наличие токена
    if not settings.TELEGRAM_BOT_TOKEN:
        print(f"[NOTIFIER ERROR] TELEGRAM_BOT_TOKEN не установлен!")
        return False
    
    try:
        import telebot

        bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode=None)
        bot.send_message(chat_id, text)
        print(f"[NOTIFIER SUCCESS] Сообщение отправлено в Telegram: {text[:50]}...")
        return True
    except Exception as e:
        # Выводим ошибку для диагностики
        print(f"[NOTIFIER ERROR] Ошибка отправки Telegram: {type(e).__name__}: {str(e)}")
        print(f"[NOTIFIER ERROR] Token: {settings.TELEGRAM_BOT_TOKEN[:10]}... (первые 10 символов)")
        print(f"[NOTIFIER ERROR] Chat ID: {chat_id}")
        return False


def _format_username(username: str) -> str:
    if not username:
        return ""
    if username.startswith("@"):  # keep single @
        return username
    return f"@{username}"


def _notifier_loop() -> None:
    print("[NOTIFIER] 🚀 Фоновый поток уведомлений запущен")
    print(f"[NOTIFIER] Токен бота: {settings.TELEGRAM_BOT_TOKEN[:10]}... (первые 10 символов)")
    iteration = 0
    while True:
        try:
            # Ensure DB connections are valid in this background thread
            close_old_connections()
            now = timezone.now()
            iteration += 1
            
            # Каждые 60 итераций (примерно 10 минут) выводим статус
            if iteration % 60 == 0:
                print(f"[NOTIFIER] Работаю... Текущее время: {timezone.localtime(now).strftime('%Y-%m-%d %H:%M:%S')}")
            
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
                    # Получаем chat_id из профиля учителя
                    if not lesson.teacher.telegram_chat_id:
                        print(f"[NOTIFIER] Пропуск урока {lesson.id}: нет telegram_chat_id у учителя {lesson.teacher.username}")
                        continue

                    local_time = timezone.localtime(lesson.start_time)
                    msg = (
                        f"занятие в {local_time.strftime('%H:%M')} через час у '{lesson.student.name}'"
                    )
                    print(f"[NOTIFIER] Найдено занятие за час: {lesson.student.name} в {local_time.strftime('%H:%M')}")
                    if _send_message_to_chat(msg, lesson.teacher.telegram_chat_id):
                        # После отправки уведомления за час - удаляем занятие, но оставляем ученика
                        print(f"[NOTIFIER] Удаление занятия {lesson.id} после отправки уведомления")
                        lesson.delete()
                    else:
                        print(f"[NOTIFIER] Не удалось отправить уведомление за час для занятия {lesson.id}")
                except Exception as e:
                    print(f"[NOTIFIER ERROR] Ошибка при обработке уведомления за час: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # 5 minutes notice
            qs_5m = Lesson.objects.filter(
                start_time__gte=lower + timedelta(minutes=5),
                start_time__lte=upper + timedelta(minutes=5),
                notified_five_minutes=False,
            )
            for lesson in qs_5m:
                try:
                    if not lesson.teacher.telegram_chat_id:
                        print(f"[NOTIFIER] Пропуск урока {lesson.id}: нет telegram_chat_id у учителя {lesson.teacher.username}")
                        continue

                    local_time = timezone.localtime(lesson.start_time)
                    msg = (
                        f"занятие в {local_time.strftime('%H:%M')} через 5 минут у '{lesson.student.name}'"
                    )
                    print(f"[NOTIFIER] Найдено занятие за 5 минут: {lesson.student.name} в {local_time.strftime('%H:%M')}")
                    if _send_message_to_chat(msg, lesson.teacher.telegram_chat_id):
                        lesson.notified_five_minutes = True
                        lesson.save(update_fields=["notified_five_minutes", "updated_at"])
                        print(f"[NOTIFIER] Уведомление за 5 минут отправлено для занятия {lesson.id}")
                    else:
                        print(f"[NOTIFIER] Не удалось отправить уведомление за 5 минут для занятия {lesson.id}")
                except Exception as e:
                    print(f"[NOTIFIER ERROR] Ошибка при обработке уведомления за 5 минут: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            # Never let the loop die; но выводим ошибку для диагностики
            print(f"[NOTIFIER ERROR] Критическая ошибка в цикле: {type(e).__name__}: {str(e)}")
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


