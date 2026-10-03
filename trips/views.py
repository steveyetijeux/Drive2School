from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from reservations.models import Reservation
from .forms import TripForm
from .models import Trip
from .utils import trip_is_finished


def trip_list(request):
    query = request.GET.get("q", "").strip()
    selected_date = request.GET.get("date", "").strip()
    all_trips = Trip.objects.select_related("driver").all()

    if query:
        all_trips = all_trips.filter(
            Q(departure__icontains=query)
            | Q(destination__icontains=query)
            | Q(description__icontains=query)
        )
    if selected_date:
        all_trips = all_trips.filter(date=selected_date)

    upcoming_trips, archived_trips = [], []
    for trip in all_trips:
        (archived_trips if trip_is_finished(trip) else upcoming_trips).append(trip)

    upcoming_trips.sort(key=lambda t: (t.date, t.departure_time))
    archived_trips.sort(key=lambda t: (t.date, t.arrival_time), reverse=True)

    return render(request, "trips/trip_list.html", {
        "trips": upcoming_trips,
        "archived_trips": archived_trips,
        "query": query,
        "selected_date": selected_date,
    })


def trip_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related("driver"), pk=pk)
    user_reservation = None
    if request.user.is_authenticated:
        user_reservation = Reservation.objects.filter(
            trip=trip, passenger=request.user
        ).first()

    passenger_reservations = []
    if request.user.is_authenticated and request.user == trip.driver:
        passenger_reservations = (
            Reservation.objects.select_related("passenger")
            .filter(trip=trip).order_by("created_at")
        )

    return render(request, "trips/trip_detail.html", {
        "trip": trip,
        "user_reservation": user_reservation,
        "passenger_reservations": passenger_reservations,
        "trip_finished": trip_is_finished(trip),
    })


@login_required
def trip_create(request):
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.driver = request.user
            trip.save()
            messages.success(request, "Votre trajet a été publié.")
            return redirect("trip_detail", pk=trip.pk)
    else:
        form = TripForm()
    return render(request, "trips/trip_form.html", {"form": form, "title": "Publier un trajet"})


@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)
    if trip_is_finished(trip):
        messages.error(request, "Un trajet archivé ne peut plus être modifié.")
        return redirect("trip_detail", pk=trip.pk)
    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre trajet a été modifié.")
            return redirect("trip_detail", pk=trip.pk)
    else:
        form = TripForm(instance=trip)
    return render(request, "trips/trip_form.html", {"form": form, "title": "Modifier le trajet"})


@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)
    if request.method == "POST":
        trip.delete()
        messages.success(request, "Le trajet a été supprimé.")
        return redirect("trip_list")
    return render(request, "trips/trip_confirm_delete.html", {"trip": trip})
