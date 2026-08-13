from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from trips.models import Trip

from .models import Reservation


@login_required
def reservation_create(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)

    if request.method != "POST":
        return redirect("trip_detail", pk=trip_id)

    if trip.driver_id == request.user.id:
        messages.error(request, "Vous conduisez déjà ce trajet.")
        return redirect("trip_detail", pk=trip.id)

    pickup_address = request.POST.get("pickup_address", "").strip()
    dropoff_address = request.POST.get("dropoff_address", "").strip()

    if not pickup_address or not dropoff_address:
        messages.error(
            request,
            "Veuillez renseigner votre adresse de montée et votre adresse de descente.",
        )
        return redirect("trip_detail", pk=trip.id)

    existing = Reservation.objects.filter(
        trip=trip,
        passenger=request.user,
    ).first()

    if existing and existing.status == Reservation.STATUS_CONFIRMED:
        messages.info(request, "Vous avez déjà réservé ce trajet.")
        return redirect("trip_detail", pk=trip.id)

    with transaction.atomic():
        trip = Trip.objects.select_for_update().get(pk=trip.id)

        active_count = Reservation.objects.filter(
            trip=trip,
            status=Reservation.STATUS_CONFIRMED,
        ).count()

        if active_count >= trip.max_seats:
            messages.error(request, "Ce trajet est complet.")
            return redirect("trip_detail", pk=trip.id)

        if existing:
            existing.status = Reservation.STATUS_CONFIRMED
            existing.pickup_address = pickup_address
            existing.dropoff_address = dropoff_address
            existing.save(
                update_fields=[
                    "status",
                    "pickup_address",
                    "dropoff_address",
                ]
            )
        else:
            Reservation.objects.create(
                trip=trip,
                passenger=request.user,
                pickup_address=pickup_address,
                dropoff_address=dropoff_address,
                status=Reservation.STATUS_CONFIRMED,
            )

    messages.success(request, "Votre place est réservée.")
    return redirect("trip_detail", pk=trip.id)


@login_required
def reservation_cancel(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        pk=reservation_id,
        passenger=request.user,
    )

    if request.method == "POST":
        reservation.status = Reservation.STATUS_CANCELLED
        reservation.save(update_fields=["status"])
        messages.success(request, "Votre réservation a été annulée.")

    return redirect("dashboard")


@login_required
def my_reservations(request):
    reservations = (
        Reservation.objects
        .select_related(
            "trip",
            "trip__driver",
        )
        .filter(
            passenger=request.user,
            status=Reservation.STATUS_CONFIRMED,
        )
    )

    return render(
        request,
        "reservations/my_reservations.html",
        {"reservations": reservations},
    )