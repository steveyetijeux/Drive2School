from django.contrib.auth.models import User
from django.db import models


class PointTransaction(models.Model):
    TYPE_TRIP = "trip"
    TYPE_PASSENGER = "passenger"

    TYPE_CHOICES = [
        (TYPE_TRIP, "Trajet effectué"),
        (TYPE_PASSENGER, "Passager transporté"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="point_transactions",
    )

    points = models.PositiveIntegerField()

    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )

    description = models.CharField(max_length=255)

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="point_transactions",
    )

    reservation = models.ForeignKey(
        "reservations.Reservation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="point_transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "trip", "transaction_type"],
                name="unique_user_trip_point_type",
            )
        ]

    def __str__(self):
        return f"{self.user.username} : +{self.points} points"