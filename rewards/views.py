from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from reservations.models import Reservation
from trips.models import Trip

from .models import PointTransaction


REWARD_LEVELS = [
    (25, "Badge Pilote"),
    (50, "Petite surprise"),
    (100, "Récompense intermédiaire"),
    (200, "Grande récompense"),
    (300, "Récompense spéciale"),
    (500, "Shooting photo personnalisé 📸"),
]


def trip_is_finished(trip):
    current_time = timezone.localtime()

    trip_datetime = timezone.make_aware(
        datetime.combine(
            trip.date,
            trip.arrival_time,
        ),
        timezone.get_current_timezone(),
    )

    return trip_datetime <= current_time


def award_points_for_finished_trips(user=None):
    trips = Trip.objects.all()

    if user is not None:
        trips = trips.filter(driver=user)

    for trip in trips:
        if not trip_is_finished(trip):
            continue

        # +1 point pour le conducteur
        PointTransaction.objects.get_or_create(
            user=trip.driver,
            trip=trip,
            transaction_type=PointTransaction.TYPE_TRIP,
            defaults={
                "points": 1,
                "description": (
                    f"Trajet effectué : "
                    f"{trip.departure} → {trip.destination}"
                ),
            },
        )

        # +2 points pour chaque passager confirmé
        reservations = (
            Reservation.objects
            .filter(
                trip=trip,
                status=Reservation.STATUS_CONFIRMED,
            )
            .select_related("passenger")
        )

        for reservation in reservations:
            PointTransaction.objects.get_or_create(
                user=reservation.passenger,
                trip=trip,
                transaction_type=PointTransaction.TYPE_PASSENGER,
                defaults={
                    "points": 2,
                    "reservation": reservation,
                    "description": (
                        f"Passager transporté : "
                        f"{trip.departure} → {trip.destination}"
                    ),
                },
            )


def get_user_points(user):
    return (
        PointTransaction.objects
        .filter(user=user)
        .aggregate(total=Sum("points"))["total"]
        or 0
    )


def get_next_reward(user_points):
    for threshold, name in REWARD_LEVELS:
        if user_points < threshold:
            return {
                "points": threshold,
                "name": name,
                "remaining": threshold - user_points,
            }

    return None


@login_required
def rewards_dashboard(request):
    award_points_for_finished_trips()

    user_points = get_user_points(request.user)

    leaderboard = (
        User.objects
        .annotate(total_points=models.Sum("point_transactions__points"))
        .order_by("-total_points", "username")
    )

    transactions = (
        PointTransaction.objects
        .filter(user=request.user)
        .select_related("trip")
    )[:20]

    next_reward = None

    for threshold, name in REWARD_LEVELS:
        if user_points < threshold:
            next_reward = {
                "points": threshold,
                "name": name,
                "remaining": threshold - user_points,
            }
            break

    return render(
        request,
        "rewards/rewards.html",
        {
            "user_points": user_points,
            "leaderboard": leaderboard,
            "transactions": transactions,
            "next_reward": next_reward,
        },
    )