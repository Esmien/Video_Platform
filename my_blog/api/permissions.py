from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Video


class IsPublishedOrOwner(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Video) -> bool:
        if obj.is_published:
            return True

        return bool(request.user.is_authenticated and obj.owner == request.user)