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


# ============================================================
# RÉCOMPENSES
# ============================================================

REWARD_LEVELS = [
    (25, "Badge Pilote"),
    (50, "Petite surprise"),
    (100, "Récompense intermédiaire"),
    (200, "Grande récompense"),
    (300, "Récompense spéciale"),
    (500, "Shooting photo personnalisé 📸"),
]


# ============================================================
# BADGES CONDUCTEUR
# ============================================================

DRIVER_BADGES = [
    {
        "points": 25,
        "name": "Pilote",
        "icon": "🥉",
        "description": (
            "Vous commencez à vous faire une place "
            "dans la communauté."
        ),
        "level": 1,
    },
    {
        "points": 50,
        "name": "Pilote confirmé",
        "icon": "🥈",
        "description": (
            "Un conducteur fiable et régulier."
        ),
        "level": 2,
    },
    {
        "points": 100,
        "name": "Pilote expert",
        "icon": "🥇",
        "description": (
            "Vous êtes devenu un conducteur incontournable."
        ),
        "level": 3,
    },
    {
        "points": 200,
        "name": "Pilote Drive2School",
        "icon": "🏆",
        "description": (
            "Un véritable pilier de la communauté Drive2School."
        ),
        "level": 4,
    },
]


# ============================================================
# TRAJET TERMINÉ ?
# ============================================================

def trip_is_finished(trip):
    """
    Retourne True si le trajet est terminé.

    Le trajet est considéré comme terminé lorsque
    son heure d'arrivée est dépassée.
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


# ============================================================
# ATTRIBUTION DES POINTS
# ============================================================

def award_points_for_finished_trips(user=None):
    """
    Attribue automatiquement les points pour les trajets terminés.

    CONDUCTEUR :
        +1 point par trajet terminé
        +2 points par passager confirmé transporté

    PASSAGER :
        Aucun point pour le moment.

    get_or_create() empêche les doublons.
    """

    trips = Trip.objects.all()

    if user is not None:
        trips = trips.filter(driver=user)

    for trip in trips:

        # --------------------------------------------------------
        # Le trajet doit être terminé
        # --------------------------------------------------------

        if not trip_is_finished(trip):
            continue

        # --------------------------------------------------------
        # Récupération des passagers confirmés
        # --------------------------------------------------------

        reservations = (
            Reservation.objects
            .filter(
                trip=trip,
                status=Reservation.STATUS_CONFIRMED,
            )
            .select_related("passenger")
        )

        passenger_count = reservations.count()

        # --------------------------------------------------------
        # CONDUCTEUR : +1 point pour le trajet
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # CONDUCTEUR : +2 points par passager
        # --------------------------------------------------------

        if passenger_count > 0:

            passenger_points = passenger_count * 2

            PointTransaction.objects.get_or_create(
                user=trip.driver,
                trip=trip,
                transaction_type=PointTransaction.TYPE_PASSENGER,
                defaults={
                    "points": passenger_points,
                    "description": (
                        f"{passenger_count} passager"
                        f"{'s' if passenger_count > 1 else ''} "
                        f"transporté"
                        f"{'s' if passenger_count > 1 else ''} : "
                        f"{trip.departure} → {trip.destination}"
                    ),
                },
            )


# ============================================================
# POINTS D'UN UTILISATEUR
# ============================================================

def get_user_points(user):
    """
    Retourne le nombre total de points conducteur
    d'un utilisateur.

    Les points pris en compte sont :
        - TYPE_TRIP
        - TYPE_PASSENGER
    """

    return (
        PointTransaction.objects
        .filter(
            user=user,
            transaction_type__in=[
                PointTransaction.TYPE_TRIP,
                PointTransaction.TYPE_PASSENGER,
            ],
        )
        .aggregate(
            total=Coalesce(
                Sum("points"),
                Value(0),
            )
        )["total"]
    )


# ============================================================
# BADGE ACTUEL DU CONDUCTEUR
# ============================================================

def get_driver_badge(points):
    """
    Retourne le badge conducteur correspondant
    au nombre de points.
    """

    current_badge = None

    for badge in DRIVER_BADGES:
        if points >= badge["points"]:
            current_badge = badge
        else:
            break

    return current_badge


# ============================================================
# PROCHAIN BADGE
# ============================================================

def get_next_driver_badge(points):
    """
    Retourne le prochain badge à débloquer.
    """

    for badge in DRIVER_BADGES:
        if points < badge["points"]:
            return {
                "points": badge["points"],
                "name": badge["name"],
                "icon": badge["icon"],
                "remaining": badge["points"] - points,
            }

    return None


# ============================================================
# PAGE REWARDS
# ============================================================

@login_required
def rewards_dashboard(request):
    """
    Page principale des récompenses.
    """

    # --------------------------------------------------------
    # Mise à jour des points des trajets terminés
    # --------------------------------------------------------

    award_points_for_finished_trips()

    # --------------------------------------------------------
    # Points de l'utilisateur connecté
    # --------------------------------------------------------

    user_points = get_user_points(request.user)

    # --------------------------------------------------------
    # Badge actuel
    # --------------------------------------------------------

    driver_badge = get_driver_badge(user_points)

    # --------------------------------------------------------
    # Prochain badge
    # --------------------------------------------------------

    next_driver_badge = get_next_driver_badge(user_points)

    # ========================================================
    # CLASSEMENT
    # ========================================================

    leaderboard = (
        User.objects
        .exclude(username="Test")
        .annotate(
            total_points=Coalesce(
                Sum(
                    "point_transactions__points",
                    filter=None,
                ),
                Value(0),
            )
        )
        .order_by(
            "-total_points",
            "username",
        )
    )

    # ========================================================
    # HISTORIQUE DES TRANSACTIONS
    # ========================================================

    transactions = (
        PointTransaction.objects
        .filter(user=request.user)
        .select_related("trip")
        .order_by("-created_at")
    )[:20]

    # ========================================================
    # PROCHAINE RÉCOMPENSE
    # ========================================================

    next_reward = None

    for threshold, name in REWARD_LEVELS:
        if user_points < threshold:
            next_reward = {
                "points": threshold,
                "name": name,
                "remaining": threshold - user_points,
            }
            break

    # ========================================================
    # AFFICHAGE
    # ========================================================

    return render(
        request,
        "rewards/rewards.html",
        {
            "user_points": user_points,
            "leaderboard": leaderboard,
            "transactions": transactions,
            "next_reward": next_reward,
            "reward_levels": REWARD_LEVELS,
            "driver_badge": driver_badge,
            "next_driver_badge": next_driver_badge,
        },
    )