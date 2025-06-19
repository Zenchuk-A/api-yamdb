from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
    SAFE_METHODS,
    IsAuthenticatedOrReadOnly,
)


class IsAdmin(IsAuthenticated):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (
            request.user.is_admin or view.kwargs.get('username', None) == 'me'
        )


class ReadOnly(BasePermission):

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsAuthorOrModeratorOrReadOnly(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_admin
            or request.user.is_moderator
            or obj.author == request.user
        )
