from datetime import datetime
from django.utils import timezone


def trip_is_finished(trip):
    """Un trajet est archivé lorsque son heure d'arrivée est passée."""
    arrival = timezone.make_aware(
        datetime.combine(trip.date, trip.arrival_time),
        timezone.get_current_timezone(),
    )
    return arrival <= timezone.localtime()
