from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import LessonForm
from .models import Lesson


def lessons_list(request):
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            # Convert naive datetime from HTML input (treated as Europe/Moscow) to aware
            dt = lesson.start_time
            if timezone.is_naive(dt):
                lesson.start_time = timezone.make_aware(dt, timezone.get_default_timezone())
            lesson.notified_one_hour = False
            lesson.notified_five_minutes = False
            lesson.save()
            return redirect("lessons_list")
    else:
        form = LessonForm()

    lessons = Lesson.objects.all()
    return render(request, "lessons/list.html", {"form": form, "lessons": lessons})


