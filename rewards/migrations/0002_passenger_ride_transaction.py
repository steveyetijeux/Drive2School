from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rewards", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pointtransaction",
            name="transaction_type",
            field=models.CharField(
                choices=[
                    ("trip", "Trajet effectué"),
                    ("passenger", "Passager transporté (conducteur)"),
                    ("passenger_ride", "Trajet effectué en tant que passager"),
                ],
                max_length=30,
            ),
        ),
    ]
