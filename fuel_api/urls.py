from django.urls import path, re_path

from fuel_api.views import InteractiveMapView, RouteFuelPlanAPIView

urlpatterns = [
    path("api/route/", RouteFuelPlanAPIView.as_view(), name="api-route-plan"),
    path("api/route", RouteFuelPlanAPIView.as_view()),
    re_path(r"^api/route/?\s*$", RouteFuelPlanAPIView.as_view()),
    path("map/", InteractiveMapView.as_view(), name="interactive-map"),
    path("map", InteractiveMapView.as_view()),
    re_path(r"^map/?\s*$", InteractiveMapView.as_view()),
    path("", InteractiveMapView.as_view(), name="home-map"),
]
