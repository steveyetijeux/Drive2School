from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
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
    """
    Retourne True si le trajet est terminé.
    """
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
    """
    Attribue automatiquement les points pour les trajets terminés.

    Conducteur :
        +1 point par trajet terminé.

    Passager :
        +2 points par réservation confirmée sur un trajet terminé.

    get_or_create() empêche d'attribuer plusieurs fois les mêmes points.
    """

    trips = Trip.objects.all()

    if user is not None:
        trips = trips.filter(driver=user)

    for trip in trips:
        if not trip_is_finished(trip):
            continue

        # ============================================================
        # CONDUCTEUR : +1 point
        # ============================================================

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

        # ============================================================
        # PASSAGERS : +2 points
        # ============================================================

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
    """
    Retourne le nombre total de points d'un utilisateur.
    """

    return (
        PointTransaction.objects
        .filter(user=user)
        .aggregate(
            total=Coalesce(
                Sum("points"),
                Value(0),
            )
        )["total"]
    )


@login_required
def rewards_dashboard(request):
    """
    Page principale des récompenses.
    """

    # Vérifie les trajets terminés et attribue les points nécessaires.
    award_points_for_finished_trips()

    # ============================================================
    # POINTS DE L'UTILISATEUR CONNECTÉ
    # ============================================================

    user_points = get_user_points(request.user)

    # ============================================================
    # CLASSEMENT
    # ============================================================

    leaderboard = (
        User.objects
        .exclude(username="Test")
        .annotate(
            total_points=Coalesce(
                Sum("point_transactions__points"),
                Value(0),
            )
        )
        .order_by("-total_points", "username")
    )

    # ============================================================
    # HISTORIQUE DES TRANSACTIONS
    # ============================================================

    transactions = (
        PointTransaction.objects
        .filter(user=request.user)
        .select_related("trip")
        .order_by("-created_at")
    )[:20]

    # ============================================================
    # PROCHAINE RÉCOMPENSE
    # ============================================================

    next_reward = None

    for threshold, name in REWARD_LEVELS:
        if user_points < threshold:
            next_reward = {
                "points": threshold,
                "name": name,
                "remaining": threshold - user_points,
            }
            break

    # ============================================================
    # AFFICHAGE
    # ============================================================

    return render(
        request,
        "rewards/rewards.html",
        {
            "user_points": user_points,
            "leaderboard": leaderboard,
            "transactions": transactions,
            "next_reward": next_reward,
            "reward_levels": REWARD_LEVELS,
        },
    )