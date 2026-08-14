from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from trips.models import Trip


class Reservation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_CONFIRMED, "Acceptée"),
        (STATUS_REJECTED, "Refusée"),
        (STATUS_CANCELLED, "Annulée"),
    ]

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Trajet",
    )

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Passager",
    )

    pickup_address = models.CharField(
        "Adresse de montée",
        max_length=255,
    )

    dropoff_address = models.CharField(
        "Adresse de descente",
        max_length=255,
    )

    status = models.CharField(
        "Statut",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trip", "passenger"],
                name="unique_active_trip_passenger",
            )
        ]
        ordering = ["-created_at"]

    def clean(self):
        if self.trip.driver_id == self.passenger_id:
            raise ValidationError(
                "Le conducteur ne peut pas réserver son propre trajet."
            )

        if (
            self.status == self.STATUS_CONFIRMED
            and self.trip.remaining_seats <= 0
            and not self.pk
        ):
            raise ValidationError("Ce trajet est complet.")

    def __str__(self):
        return f"{self.passenger.username} - {self.trip}"