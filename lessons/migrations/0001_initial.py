from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_name", models.CharField(max_length=255)),
                ("tg_username", models.CharField(blank=True, help_text="@username без @ тоже ок", max_length=255)),
                ("start_time", models.DateTimeField()),
                ("notified_one_hour", models.BooleanField(default=False)),
                ("notified_five_minutes", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["start_time"]},
        ),
    ]


