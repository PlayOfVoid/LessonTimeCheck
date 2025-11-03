from django.contrib import admin
from django import forms

from .models import Teacher, Student, Lesson


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("username", "telegram_chat_id", "created_at")
    search_fields = ("username",)
    fields = ("username", "password", "telegram_chat_id")
    
    def save_model(self, request, obj, form, change):
        # Если пароль изменен или новый объект
        if 'password' in form.changed_data or not change:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "created_at")
    list_filter = ("teacher",)
    search_fields = ("name",)
    fields = ("name", "teacher", "bio")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("student", "teacher", "start_time", "notified_one_hour", "notified_five_minutes")
    list_filter = ("teacher", "notified_one_hour", "notified_five_minutes")
    search_fields = ("student__name",)
    ordering = ("start_time",)


