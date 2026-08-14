from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("trips/", include("trips.urls")),
    path("reservations/", include("reservations.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("rewards/", include("rewards.urls")),
]
