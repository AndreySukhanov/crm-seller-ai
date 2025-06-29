from django.urls import path

from . import views

urlpatterns = [
    path("stats/", views.stats_view),
    path("stats_data/", views.StatsView.as_view()),
]
