from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "departure",
        "destination",
        "date",
        "departure_time",
        "arrival_time",
        "driver",
        "max_seats",
        "created_at",
    )
    list_filter = ("date", "departure", "destination")
    search_fields = ("departure", "destination", "driver__username")
    ordering = ("date", "departure_time")
