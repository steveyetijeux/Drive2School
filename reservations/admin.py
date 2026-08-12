from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("trip", "passenger", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = (
        "passenger__username",
        "trip__departure",
        "trip__destination",
    )
