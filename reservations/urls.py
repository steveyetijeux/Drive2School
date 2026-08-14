from django.urls import path

from .views import (
    my_reservations,
    reservation_accept,
    reservation_cancel,
    reservation_create,
    reservation_reject,
)

urlpatterns = [
    path(
        "trip/<int:trip_id>/reserve/",
        reservation_create,
        name="reservation_create",
    ),
    path(
        "<int:reservation_id>/accept/",
        reservation_accept,
        name="reservation_accept",
    ),
    path(
        "<int:reservation_id>/reject/",
        reservation_reject,
        name="reservation_reject",
    ),
    path(
        "<int:reservation_id>/cancel/",
        reservation_cancel,
        name="reservation_cancel",
    ),
    path(
        "mine/",
        my_reservations,
        name="my_reservations",
    ),
]