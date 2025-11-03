from django.urls import path

from . import views


urlpatterns = [
    path("", views.students_list, name="home"),
    path("login/", views.teacher_login, name="teacher_login"),
    path("logout/", views.teacher_logout, name="logout"),
    path("students/", views.students_list, name="students_list"),
    path("students/<int:student_id>/", views.student_detail, name="student_detail"),
    path("students/<int:student_id>/bio/pdf/", views.student_bio_pdf, name="student_bio_pdf"),
    path("settings/", views.settings_page, name="settings_page"),
]
