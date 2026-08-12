from django.urls import path

from . import views

urlpatterns = [
    path(
        "trip/<int:trip_id>/reserve/",
        views.reservation_create,
        name="reservation_create",
    ),
    path(
        "<int:reservation_id>/cancel/",
        views.reservation_cancel,
        name="reservation_cancel",
    ),
    path(
        "mine/",
        views.my_reservations,
        name="my_reservations",
    ),
]
