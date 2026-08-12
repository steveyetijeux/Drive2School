from django import forms

from .models import Trip


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = (
            "departure",
            "destination",
            "date",
            "departure_time",
            "arrival_time",
            "max_seats",
            "description",
        )
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "departure_time": forms.TimeInput(attrs={"type": "time"}),
            "arrival_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        departure = cleaned.get("departure_time")
        arrival = cleaned.get("arrival_time")
        if departure and arrival and arrival <= departure:
            self.add_error(
                "arrival_time",
                "L'heure d'arrivée doit être après l'heure de départ.",
            )
        return cleaned
