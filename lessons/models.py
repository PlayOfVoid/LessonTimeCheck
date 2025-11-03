from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


class Teacher(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)  # Хранится как хеш
    telegram_chat_id = models.CharField(max_length=50, blank=True, help_text="Telegram Chat ID для уведомлений")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # Если пароль не захеширован, хешируем его
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Student(models.Model):
    name = models.CharField(max_length=255, help_text="Например: Армен(Ансар)")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='students')
    bio = models.TextField(blank=True, help_text="Markdown разметка поддерживается")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [['name', 'teacher']]

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"


class Lesson(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lessons')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons')
    start_time = models.DateTimeField()

    notified_one_hour = models.BooleanField(default=False)
    notified_five_minutes = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self) -> str:
        return f"{self.student.name} @ {timezone.localtime(self.start_time).strftime('%Y-%m-%d %H:%M')}"


