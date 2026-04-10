from django.db import models
from django.conf import settings
from django.utils import timezone
# ---------- RBAC MODELS ----------

class Permission(models.Model):
    """Define a system permission."""

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(models.Model):
    """User roles like Admin, Manager, Support, etc."""

    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField(
        Permission, through="RolePermission", related_name="roles"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def has_permission(self, permission_code):
        """Check if role has a specific permission."""
        return self.permissions.filter(code=permission_code, is_active=True).exists()

    

class RolePermission(models.Model):
    """Link roles with permissions."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.name} -> {self.permission.name}"


class UserRole(models.Model):
    """Assign roles to users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(default=timezone.now)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_roles"
    )

    class Meta:
        unique_together = ("user", "role")

    def __str__(self):
        return f"{self.user.email} -> {self.role.name}"

# ---------- RBAC HELPER METHODS ----------


def assign_role(user, role_name, assigned_by=None):
    """Assign a role to a user."""
    try:
        role = Role.objects.get(name=role_name, is_active=True)
        user_role, created = UserRole.objects.get_or_create(
            user=user, 
            role=role,
            defaults={'assigned_by': assigned_by}
        )
        return user_role, created
    except Role.DoesNotExist:
        return None, False


def remove_role(user, role_name):
    """Remove a role from user."""
    return UserRole.objects.filter(user=user, role__name=role_name).delete()


def user_has_role(user, role_name):
    """Check if user has a specific role."""
    return user.user_roles.filter(role__name=role_name, role__is_active=True).exists()


def user_has_permission(user, permission_code):
    """Check if user has a specific permission."""
    return RolePermission.objects.filter(
        role__user_roles__user=user, 
        permission__code=permission_code,
        role__is_active=True,
        permission__is_active=True
    ).exists()


def get_user_roles(user):
    """Get all active roles for a user."""
    return user.user_roles.filter(role__is_active=True).select_related('role')


def get_user_permissions(user):
    """Get all permissions for a user through their roles."""
    return Permission.objects.filter(
        roles__user_roles__user=user,
        is_active=True
    ).distinct()





def create_role(name, permissions=None, dashboard_config=None):
    """Create a new role with permissions and dashboard config."""
    role = Role.objects.create(
        name=name,
        dashboard_config=dashboard_config or {}
    )
    
    if permissions:
        role.permissions.set(permissions)
    
    return role


def create_permission(code, name):
    """Create a new permission."""
    return Permission.objects.create(
        code=code,
        name=name,
    )




'''
# Example use in Views
class UserListView(APIView):
    def get(self, request):
        if not user_has_permission(request.user, "view_users"):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        # normal logic
        return Response({"message": "Here are all users."})
'''
