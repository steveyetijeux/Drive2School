from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TripForm
from .models import Trip


def trip_list(request):
    trips = Trip.objects.select_related("driver").all()

    query = request.GET.get("q", "").strip()
    date = request.GET.get("date", "").strip()

    if query:
        trips = trips.filter(
            Q(departure__icontains=query)
            | Q(destination__icontains=query)
            | Q(description__icontains=query)
        )

    if date:
        trips = trips.filter(date=date)

    return render(
        request,
        "trips/trip_list.html",
        {"trips": trips, "query": query, "selected_date": date},
    )


def trip_detail(request, pk):
    trip = get_object_or_404(
        Trip.objects.select_related("driver"),
        pk=pk,
    )
    return render(request, "trips/trip_detail.html", {"trip": trip})


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

    return render(
        request,
        "trips/trip_form.html",
        {"form": form, "title": "Publier un trajet"},
    )


@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)

    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre trajet a été modifié.")
            return redirect("trip_detail", pk=trip.pk)
    else:
        form = TripForm(instance=trip)

    return render(
        request,
        "trips/trip_form.html",
        {"form": form, "title": "Modifier le trajet"},
    )


@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)

    if request.method == "POST":
        trip.delete()
        messages.success(request, "Le trajet a été supprimé.")
        return redirect("trip_list")

    return render(request, "trips/trip_confirm_delete.html", {"trip": trip})
