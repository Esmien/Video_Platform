from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VideoViewSet, RegisterView

router = DefaultRouter()

router.register(prefix='videos', viewset=VideoViewSet, basename='video')

urlpatterns = [
    path(route='', view=include(router.urls)),
    path(route='register/', view=RegisterView.as_view(), name='register')
]