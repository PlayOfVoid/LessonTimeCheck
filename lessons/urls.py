from django.urls import path

from . import views


urlpatterns = [
    path("", views.lessons_list, name="lessons_list"),
]


