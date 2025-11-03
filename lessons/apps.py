from django.apps import AppConfig


class LessonsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lessons"

    def ready(self) -> None:
        # Start background notifier thread once
        from .notifier import start_notifier_once

        start_notifier_once()


