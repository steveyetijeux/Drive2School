from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("departure", models.CharField(max_length=150, verbose_name="Lieu de départ")),
                ("destination", models.CharField(max_length=150, verbose_name="Destination")),
                ("date", models.DateField(verbose_name="Date")),
                ("departure_time", models.TimeField(verbose_name="Heure de départ")),
                ("arrival_time", models.TimeField(verbose_name="Heure d'arrivée")),
                ("max_seats", models.PositiveIntegerField(default=4, verbose_name="Places disponibles")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("driver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trips", to=settings.AUTH_USER_MODEL, verbose_name="Conducteur")),
            ],
            options={"ordering": ["date", "departure_time"]},
        ),
    ]
