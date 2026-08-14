from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from trips.models import Trip

from .models import Reservation


@login_required
def reservation_create(request, trip_id):
    if request.method != "POST":
        return redirect("trip_detail", pk=trip_id)

    trip = get_object_or_404(Trip, pk=trip_id)

    if trip.driver_id == request.user.id:
        messages.error(
            request,
            "Vous conduisez déjà ce trajet.",
        )
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

    if existing:
        if existing.status == Reservation.STATUS_CONFIRMED:
            messages.info(
                request,
                "Votre réservation pour ce trajet est déjà acceptée.",
            )
            return redirect("trip_detail", pk=trip.id)

        if existing.status == Reservation.STATUS_PENDING:
            messages.info(
                request,
                "Votre demande de réservation est déjà en attente.",
            )
            return redirect("trip_detail", pk=trip.id)

        existing.pickup_address = pickup_address
        existing.dropoff_address = dropoff_address
        existing.status = Reservation.STATUS_PENDING
        existing.save(
            update_fields=[
                "pickup_address",
                "dropoff_address",
                "status",
            ]
        )

        messages.success(
            request,
            "Votre nouvelle demande de réservation a été envoyée au conducteur.",
        )
        return redirect("trip_detail", pk=trip.id)

    Reservation.objects.create(
        trip=trip,
        passenger=request.user,
        pickup_address=pickup_address,
        dropoff_address=dropoff_address,
        status=Reservation.STATUS_PENDING,
    )

    messages.success(
        request,
        "Votre demande de réservation a été envoyée au conducteur.",
    )

    return redirect("trip_detail", pk=trip.id)


@login_required
def reservation_accept(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related("trip", "passenger"),
        pk=reservation_id,
    )

    if reservation.trip.driver_id != request.user.id:
        messages.error(
            request,
            "Vous n'êtes pas autorisé à gérer cette réservation.",
        )
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("dashboard")

    if reservation.status != Reservation.STATUS_PENDING:
        messages.info(
            request,
            "Cette demande n'est plus en attente.",
        )
        return redirect("dashboard")

    with transaction.atomic():
        trip = Trip.objects.select_for_update().get(pk=reservation.trip_id)

        confirmed_count = Reservation.objects.filter(
            trip=trip,
            status=Reservation.STATUS_CONFIRMED,
        ).count()

        if confirmed_count >= trip.max_seats:
            messages.error(
                request,
                "Impossible d'accepter cette demande : le trajet est complet.",
            )
            return redirect("dashboard")

        reservation.status = Reservation.STATUS_CONFIRMED
        reservation.save(update_fields=["status"])

    messages.success(
        request,
        f"La réservation de {reservation.passenger.username} a été acceptée.",
    )

    return redirect("dashboard")


@login_required
def reservation_reject(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related("trip", "passenger"),
        pk=reservation_id,
    )

    if reservation.trip.driver_id != request.user.id:
        messages.error(
            request,
            "Vous n'êtes pas autorisé à gérer cette réservation.",
        )
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("dashboard")

    if reservation.status != Reservation.STATUS_PENDING:
        messages.info(
            request,
            "Cette demande n'est plus en attente.",
        )
        return redirect("dashboard")

    reservation.status = Reservation.STATUS_REJECTED
    reservation.save(update_fields=["status"])

    messages.success(
        request,
        f"La demande de {reservation.passenger.username} a été refusée.",
    )

    return redirect("dashboard")


@login_required
def reservation_cancel(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        pk=reservation_id,
        passenger=request.user,
    )

    if request.method == "POST":
        if reservation.status in (
            Reservation.STATUS_PENDING,
            Reservation.STATUS_CONFIRMED,
        ):
            reservation.status = Reservation.STATUS_CANCELLED
            reservation.save(update_fields=["status"])

            messages.success(
                request,
                "Votre réservation a été annulée.",
            )

    return redirect("dashboard")


@login_required
def my_reservations(request):
    reservations = (
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
    )

    return render(
        request,
        "reservations/my_reservations.html",
        {"reservations": reservations},
    )