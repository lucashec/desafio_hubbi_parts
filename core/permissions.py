from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_staff)


class HasApiKey(BasePermission):
    def has_permission(self, request, view):
        api_key = request.META.get("HTTP_X_API_KEY")
        if not api_key:
            return False
        return True
