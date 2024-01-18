from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'POST':
            return True
        if request.method in ['DELETE', 'PATCH'] and request.user == obj.author:
            return True
        return False
    

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # разрешить GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # разрешить только аутентифицированным пользователям выполнять операции записи
        return request.user and request.user.is_authenticated