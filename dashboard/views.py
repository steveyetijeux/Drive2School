from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from reservations.models import Reservation
from trips.models import Trip


@login_required
def dashboard(request):
    my_trips = Trip.objects.filter(driver=request.user)
    my_reservations = Reservation.objects.select_related(
        "trip",
        "trip__driver",
    ).filter(
        passenger=request.user,
        status=Reservation.STATUS_CONFIRMED,
    )

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "my_trips": my_trips,
            "my_reservations": my_reservations,
        },
    )
