from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from gym import views
from rest_framework.routers import DefaultRouter
from gym.api import (
    UsersViewset,
    MembershipTypesViewset,
    MembershipsViewset,
    WorkoutSessionsViewset,UserProfileViewSet
)

router = DefaultRouter()
router.register("user-profile", UserProfileViewSet, basename="user-profile")
router.register("users", UsersViewset, basename="users")
router.register("membershiptype", MembershipTypesViewset, basename="membershiptype")
router.register("membership", MembershipsViewset, basename="membership")
router.register("workoutsession", WorkoutSessionsViewset, basename="workoutsession")
router.register("userprofile", UserProfileViewSet, basename="userprofile")

urlpatterns = [
    path("", views.ShowTrainerView.as_view(), name="trainers"),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
