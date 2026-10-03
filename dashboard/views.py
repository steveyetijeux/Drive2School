from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render
from django.utils import timezone

from reservations.models import Reservation
from trips.models import Trip


def _trip_is_finished(trip):
    arrival = timezone.make_aware(
        datetime.combine(trip.date, trip.arrival_time),
        timezone.get_current_timezone(),
    )
    return arrival <= timezone.localtime()


@login_required
def dashboard(request):
    all_my_trips = (
        Trip.objects.filter(driver=request.user)
        .prefetch_related(Prefetch(
            "reservations",
            queryset=Reservation.objects.select_related("passenger").order_by("-created_at"),
        ))
        .order_by("date", "departure_time")
    )
    my_trips, archived_trips = [], []
    for trip in all_my_trips:
        (archived_trips if _trip_is_finished(trip) else my_trips).append(trip)

    my_reservations = (
        Reservation.objects.select_related("trip", "trip__driver")
        .filter(passenger=request.user)
        .exclude(status=Reservation.STATUS_CANCELLED)
        .order_by("-created_at")
    )
    return render(request, "dashboard/dashboard.html", {
        "my_trips": my_trips,
        "archived_trips": archived_trips,
        "my_reservations": my_reservations,
    })
