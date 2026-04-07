from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VideoViewSet

router = DefaultRouter()

router.register(prefix='videos', viewset=VideoViewSet, basename='video')

urlpatterns = [
    path(route='', view=include(router.urls))
]