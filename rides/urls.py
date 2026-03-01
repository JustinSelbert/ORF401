from django.urls import path

from . import views

app_name = "rides"

urlpatterns = [
    path("", views.home, name="home"),
    path("rides/", views.index, name="index"),
    path("rides/<int:person_id>/", views.rider_profile, name="ride_profile"),
    path("riders/<int:person_id>/", views.rider_profile, name="rider_profile"),
    path("api/road-route/", views.road_route, name="road_route"),
    path("signin/", views.sign_in, name="sign_in"),
    path("profile/", views.profile, name="profile"),
    path("map/", views.map_view, name="map"),
    path("faq/", views.faq, name="faq"),
]
