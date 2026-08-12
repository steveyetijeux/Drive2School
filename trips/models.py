from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Trip(models.Model):
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trips",
        verbose_name="Conducteur",
    )
    departure = models.CharField("Lieu de départ", max_length=150)
    destination = models.CharField("Destination", max_length=150)
    date = models.DateField("Date")
    departure_time = models.TimeField("Heure de départ")
    arrival_time = models.TimeField("Heure d'arrivée")
    max_seats = models.PositiveIntegerField("Places disponibles", default=4)
    description = models.TextField("Description", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "departure_time"]

    def __str__(self):
        return f"{self.departure} → {self.destination}"

    @property
    def booked_seats(self):
        return self.reservations.filter(status="confirmed").count()

    @property
    def remaining_seats(self):
        return max(self.max_seats - self.booked_seats, 0)

    def clean(self):
        if self.max_seats < 1:
            raise ValidationError({"max_seats": "Le trajet doit avoir au moins une place."})
        if self.arrival_time <= self.departure_time:
            raise ValidationError(
                {"arrival_time": "L'heure d'arrivée doit être après l'heure de départ."}
            )
