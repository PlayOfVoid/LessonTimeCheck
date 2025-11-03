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
            "name": forms.TextInput(attrs={'placeholder': 'Например: Армен(Ансар)'}),
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


