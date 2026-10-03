from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from reservations.models import Reservation
from trips.models import Trip
from trips.utils import trip_is_finished
from .models import PointTransaction


REWARD_LEVELS = [
    (25, "Badge Pilote"),
    (50, "Petite surprise"),
    (100, "Récompense intermédiaire"),
    (200, "Grande récompense"),
    (300, "Récompense spéciale"),
    (500, "Shooting photo personnalisé 📸"),
]

DRIVER_BADGES = [
    {"points": 25, "name": "Pilote", "icon": "🥉", "description": "Vous commencez à vous faire une place dans la communauté.", "level": 1},
    {"points": 50, "name": "Pilote confirmé", "icon": "🥈", "description": "Un conducteur fiable et régulier.", "level": 2},
    {"points": 100, "name": "Pilote expert", "icon": "🥇", "description": "Vous êtes devenu un conducteur incontournable.", "level": 3},
    {"points": 200, "name": "Pilote Drive2School", "icon": "🏆", "description": "Un véritable pilier de la communauté Drive2School.", "level": 4},
]


def award_points_for_finished_trips(user=None):
    """Attribue une seule fois les points des trajets arrivés à destination."""
    trips = Trip.objects.select_related("driver")
    if user is not None:
        trips = trips.filter(driver=user)

    for trip in trips:
        if not trip_is_finished(trip):
            continue
        with transaction.atomic():
            PointTransaction.objects.get_or_create(
                user=trip.driver,
                trip=trip,
                transaction_type=PointTransaction.TYPE_TRIP,
                defaults={
                    "points": 1,
                    "description": f"Trajet effectué : {trip.departure} → {trip.destination}",
                },
            )

            confirmed = list(
                Reservation.objects.select_related("passenger").filter(
                    trip=trip, status=Reservation.STATUS_CONFIRMED
                )
            )
            if confirmed:
                PointTransaction.objects.get_or_create(
                    user=trip.driver,
                    trip=trip,
                    transaction_type=PointTransaction.TYPE_PASSENGER,
                    defaults={
                        "points": len(confirmed) * 2,
                        "description": (
                            f"{len(confirmed)} passager{'s' if len(confirmed) != 1 else ''} "
                            f"transporté{'s' if len(confirmed) != 1 else ''} : "
                            f"{trip.departure} → {trip.destination}"
                        ),
                    },
                )
                # Le passager gagne +1 une fois son trajet passé et sa réservation confirmée.
                for reservation in confirmed:
                    PointTransaction.objects.get_or_create(
                        user=reservation.passenger,
                        trip=trip,
                        transaction_type=PointTransaction.TYPE_PASSENGER_RIDE,
                        defaults={
                            "points": 1,
                            "reservation": reservation,
                            "description": (
                                f"Trajet effectué en tant que passager : "
                                f"{trip.departure} → {trip.destination}"
                            ),
                        },
                    )


def get_user_points(user):
    return PointTransaction.objects.filter(user=user).aggregate(
        total=Coalesce(Sum("points"), Value(0))
    )["total"]


def get_driver_badge(points):
    badge = None
    for item in DRIVER_BADGES:
        if points >= item["points"]:
            badge = item
        else:
            break
    return badge


def get_next_driver_badge(points):
    for item in DRIVER_BADGES:
        if points < item["points"]:
            return {
                "points": item["points"], "name": item["name"],
                "icon": item["icon"], "remaining": item["points"] - points,
            }
    return None


def _period_start(period, now):
    today = timezone.localdate(now)
    if period == "week":
        start_date = today - timedelta(days=today.weekday())
    elif period == "month":
        start_date = today.replace(day=1)
    else:
        return None
    return timezone.make_aware(datetime.combine(start_date, time.min), timezone.get_current_timezone())


@login_required
def rewards_dashboard(request):
    # On attribue les points des trajets arrivés à échéance avant d'afficher les totaux.
    award_points_for_finished_trips()
    user_points = get_user_points(request.user)
    period = request.GET.get("period", "all")
    if period not in {"week", "month", "all"}:
        period = "all"

    leaderboard_transactions = PointTransaction.objects.all()
    start = _period_start(period, timezone.now())
    if start is not None:
        leaderboard_transactions = leaderboard_transactions.filter(created_at__gte=start)

    leaderboard = (
        User.objects.exclude(username="Test")
        .annotate(total_points=Coalesce(
            Sum(
                "point_transactions__points",
                filter=(
                    Q(point_transactions__created_at__gte=start)
                    if start is not None else Q()
                ),
            ),
            Value(0),
        ))
        .order_by("-total_points", "username")
    )

    transactions = PointTransaction.objects.filter(user=request.user).select_related("trip").order_by("-created_at")[:20]
    next_reward = next((
        {"points": threshold, "name": name, "remaining": threshold - user_points}
        for threshold, name in REWARD_LEVELS if user_points < threshold
    ), None)

    return render(request, "rewards/rewards.html", {
        "user_points": user_points,
        "leaderboard": leaderboard,
        "transactions": transactions,
        "next_reward": next_reward,
        "reward_levels": REWARD_LEVELS,
        "driver_badge": get_driver_badge(user_points),
        "next_driver_badge": get_next_driver_badge(user_points),
        "selected_period": period,
    })
