from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render

from reservations.models import Reservation
from trips.models import Trip


@login_required
def dashboard(request):
    my_trips = (
        Trip.objects.filter(driver=request.user)
        .prefetch_related(
            Prefetch(
                "reservations",
                queryset=Reservation.objects.select_related(
                    "passenger"
                ).order_by("-created_at"),
            )
        )
        .order_by("date", "departure_time")
    )

    my_reservations = (
        Reservation.objects.select_related(
            "trip",
            "trip__driver",
        )
        .filter(
            passenger=request.user,
        )
        .exclude(
            status=Reservation.STATUS_CANCELLED,
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "my_trips": my_trips,
            "my_reservations": my_reservations,
        },
    )