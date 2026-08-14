from django.urls import path

from .views import rewards_dashboard


urlpatterns = [
    path("", rewards_dashboard, name="rewards"),
]