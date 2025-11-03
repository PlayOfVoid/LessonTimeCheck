from django import forms

from .models import Teacher, Student, Lesson


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={'placeholder': 'Например: Тимофей(Юлия)'}),
        }


class BioForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["bio"]
        widgets = {
            "bio": forms.Textarea(attrs={'rows': 20, 'placeholder': 'Используйте Markdown разметку...'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["student", "start_time"]
        widgets = {
            "student": forms.Select(attrs={'class': 'form-select'}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ProfileForm(forms.ModelForm):
    """Форма для изменения username и telegram_chat_id"""
    class Meta:
        model = Teacher
        fields = ["username", "telegram_chat_id"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Имя пользователя"}),
            "telegram_chat_id": forms.TextInput(attrs={"placeholder": "Ваш Telegram Chat ID"}),
        }


class PasswordChangeForm(forms.Form):
    """Отдельная форма для смены пароля"""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Новый пароль"}),
        required=True,
        label="Новый пароль",
        min_length=1,  # Минимум 1 символ, можно любой пароль
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Подтвердите пароль"}),
        required=True,
        label="Подтверждение пароля"
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        password_confirm = cleaned_data.get("new_password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Пароли не совпадают!")

        return cleaned_data
