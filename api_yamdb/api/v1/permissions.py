from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
    IsAuthenticatedOrReadOnly,
)


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


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


class IsAdminOrReadOnlyRole(BasePermission):

    def has_permission(self, request, view):
        if (request.method in SAFE_METHODS) or (
            request.user.is_authenticated
            and request.user.is_admin
        ):
            return True

        return True
