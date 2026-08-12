from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("trips", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Reservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("confirmed", "Confirmée"), ("cancelled", "Annulée")], default="confirmed", max_length=20, verbose_name="Statut")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("passenger", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to=settings.AUTH_USER_MODEL, verbose_name="Passager")),
                ("trip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to="trips.trip", verbose_name="Trajet")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="reservation",
            constraint=models.UniqueConstraint(fields=("trip", "passenger"), name="unique_active_trip_passenger"),
        ),
    ]
