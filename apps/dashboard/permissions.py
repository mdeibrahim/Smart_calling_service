from rest_framework import permissions
from apps.account.models import UserType


class IsAdminUser(permissions.BasePermission):
    """
    Permission class that checks if user is an admin (super_admin or admin).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type in [UserType.SUPER_ADMIN, UserType.ADMIN]


class IsManagerUser(permissions.BasePermission):
    """
    Permission class that checks if user is a manager.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == UserType.MANAGER


class IsAuditorUser(permissions.BasePermission):
    """
    Permission class that checks if user is an auditor.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == UserType.AUDITOR


class IsSalesUser(permissions.BasePermission):
    """
    Permission class that checks if user is a sales person.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == UserType.SELLS


class IsAdminOrManager(permissions.BasePermission):
    """
    Permission class that checks if user is an admin or manager.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type in [UserType.SUPER_ADMIN, UserType.ADMIN, UserType.MANAGER]


class IsAdminOrManagerOrAuditor(permissions.BasePermission):
    """
    Permission class that checks if user is an admin, manager, or auditor.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type in [
            UserType.SUPER_ADMIN, 
            UserType.ADMIN, 
            UserType.MANAGER, 
            UserType.AUDITOR
        ]


class IsSupportUser(permissions.BasePermission):
    """
    Permission class that checks if user is a support user.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == UserType.SUPPORT
